from django.db.models import Q, F, Value, Case, When, IntegerField
from django.utils import timezone
from datetime import timedelta
import re
from .models import Job

class JobSearchEngine:
    """Advanced job search with relevance scoring"""
    
    def search(self, search_params, base_queryset=None):
        """
        Perform advanced job search with relevance scoring
        """
        if base_queryset is None:
            queryset = Job.published.active()
        else:
            queryset = base_queryset
        
        queryset = self._apply_filters(queryset, search_params)
        
        # Applying search query with relevance scoring
        search_query = search_params.get('q')
        if search_query:
            queryset = self._apply_text_search(queryset, search_query)
        
        # Applying relevance scoring and ordering
        queryset = self._apply_relevance_scoring(queryset, search_params)
        
        return queryset.distinct()
      
    def _is_uuid(self, value):
      """Check if value is a valid UUID"""
      try:
          import uuid
          uuid.UUID(value)
          return True
      except (ValueError, AttributeError):
          return False
    
    def _is_numeric(self, value):
      """Check if value is numeric (for integer IDs)"""
      try:
          int(value)
          return True
      except (ValueError, TypeError):
          return False
    
    def _apply_filters(self, queryset, params):
        """Apply various filters to the queryset"""
        
        # Location filter
        location = params.get('location')
        remote_only = params.get('remote_only')
        if remote_only:
            print('Ys i am here')
            queryset = queryset.filter(remote_allowed=remote_only)
            
        elif location:
            queryset = queryset.filter(
                Q(location__icontains=location) | Q(remote_allowed=True)
            )
        
        # Job type filter
        job_types = params.get('job_type')
        if job_types:
            types_val = [t.strip().lower() for t in job_types.split(',')]
            print(types_val)
            map_keys = {key.lower(): key for key, label in Job.JOB_TYPES}
            map_labels = {label.lower(): key for key, label in Job.JOB_TYPES}
            
            t_filters = [map_keys.get(t) or map_labels.get(t) for t in types_val if t]
            queryset = queryset.filter(job_type__in=t_filters)
        
        # Experience level filter
        experience_levels = params.get('experience_level')
        if experience_levels:
          values = [v.strip().lower() for v in experience_levels.split(",")]
          mapping = {code.lower(): code for code, label in Job.EXPERIENCE_LEVELS}
          label_map = {label.lower(): code for code, label in Job.EXPERIENCE_LEVELS}
          
          filters = [mapping.get(v) or label_map.get(v) for v in values if v]
          queryset = queryset.filter(experience_level__in=filters)
        
        # Category filter
        category = params.get('category')
        if category:
            cats = [cat.strip() for cat in category.split(',')]
            cat_query = Q()
            
            for cat in cats:
              if self._is_uuid(cat) or self._is_numeric(cat):
                cat_query |= Q(category=cat)
              cat_query |= Q(category__name__icontains=cat)
            queryset = queryset.filter(cat_query)
        
        # Industry filter
        industry = params.get('industry')
        if industry:
            queries = [v.strip() for v in industry.split(',')]
            industry_query = Q()
            
            for query in queries:
              if self._is_uuid(query) or self._is_numeric(query):
                industry_query |= Q(industry=query)
              industry_query |= Q(industry__name__icontains=query)
            queryset = queryset.filter(industry_query)
        
        # Company filter
        company = params.get('company')
        if company:
            values = [v.strip() for v in company.split(',')]
            company_query = Q()
            
            for val in values:
              if self._is_uuid(value=val) or self._is_numeric(val):
                company_query |= Q(company=val)
              else:
                company_query |= Q(company__name__icontains=val)
                
            queryset = queryset.filter(company_query).distinct()
        
        # Salary filters
        salary_min = params.get('salary_min')
        salary_max = params.get('salary_max')
        
        if salary_min:
            queryset = queryset.filter(
                Q(salary_min__gte=salary_min) | 
                Q(salary_max__gte=salary_min) |
                Q(salary_min__isnull=True, salary_max__isnull=True)
            )
        
        if salary_max:
            queryset = queryset.filter(
                Q(salary_min__lte=salary_max) |
                Q(salary_max__lte=salary_max) |
                Q(salary_min__isnull=True, salary_max__isnull=True)
            )
        
        # Skills filter
        skills = params.get('skills')
        if skills:
            skills_arr = [s.strip().lower() for s in skills.split(',')]
            skills_query = Q()
            
            for skill in skills_arr:
              if self._is_uuid(skill) or self._is_numeric(skill):
                skills_query |= Q(skills__id=skill)
              skills_query |= Q(skills__name__icontains=skill)
            
            queryset = queryset.filter(skills_query).distinct()
        
        # Featured filter
        is_featured = params.get('is_featured')
        if is_featured is not None:
            queryset = queryset.filter(is_featured__icontains=is_featured)
        
        # Posted days ago filter
        posted_days_ago = params.get('posted_days_ago')
        if posted_days_ago:
            cutoff_date = timezone.now() - timedelta(days=posted_days_ago)
            queryset = queryset.filter(published_at__gte=cutoff_date)
        
        # Has salary filter
        has_salary = params.get('has_salary')
        if has_salary is not None:
            if has_salary:
                queryset = queryset.filter(
                    Q(salary_min__isnull=False) | Q(salary_max__isnull=False)
                )
            else:
                queryset = queryset.filter(
                    salary_min__isnull=True, salary_max__isnull=True
                )
        
        return queryset
    
    def _apply_text_search(self, queryset, search_query):
        """Apply text search with relevance scoring"""
        if not search_query:
            return queryset
        
        # Clean and split search query
        terms = self._extract_search_terms(search_query)
        
        search_filter = Q()
        for term in terms:
            term_filter = (
                Q(title__icontains=term) |
                Q(description__icontains=term) |
                Q(requirements__icontains=term) |
                Q(responsibilities__icontains=term) |
                Q(company__name__icontains=term) |
                Q(skills__name__icontains=term) |
                Q(category__name__icontains=term) |
                Q(industry__name__icontains=term)
            )
            search_filter &= term_filter
        
        return queryset.filter(search_filter)
    
    def _apply_relevance_scoring(self, queryset, params):
        """Apply relevance scoring and ordering"""
        search_query = params.get('q', '')
        terms = self._extract_search_terms(search_query) if search_query else []
        
        # Base relevance score
        relevance_score = Value(0, output_field=IntegerField())
        
        # Boost for exact title matches
        for term in terms:
            relevance_score = Case(
                When(title__iexact=term, then=relevance_score + 100),
                When(title__icontains=term, then=relevance_score + 50),
                default=relevance_score,
                output_field=IntegerField()
            )
        
        # Boost for company name matches
        for term in terms:
            relevance_score = Case(
                When(company__name__icontains=term, then=relevance_score + 30),
                default=relevance_score,
                output_field=IntegerField()
            )
        
        # Boost for skills matches
        for term in terms:
            relevance_score = Case(
                When(skills__name__icontains=term, then=relevance_score + 20),
                default=relevance_score,
                output_field=IntegerField()
            )
        
        # Boost for featured jobs
        relevance_score = Case(
            When(is_featured=True, then=relevance_score + 25),
            default=relevance_score,
            output_field=IntegerField()
        )
        
        # Boost for recently posted jobs
        now = timezone.now()
        relevance_score = Case(
            When(
                published_at__gte=now - timedelta(days=1),
                then=relevance_score + 15
            ),
            When(
                published_at__gte=now - timedelta(days=7),
                then=relevance_score + 10
            ),
            When(
                published_at__gte=now - timedelta(days=30),
                then=relevance_score + 5
            ),
            default=relevance_score,
            output_field=IntegerField()
        )
        
        # Boost for jobs with higher view counts (popularity)
        relevance_score = Case(
            When(views_count__gte=1000, then=relevance_score + 15),
            When(views_count__gte=500, then=relevance_score + 10),
            When(views_count__gte=100, then=relevance_score + 5),
            default=relevance_score,
            output_field=IntegerField()
        )
        
        # Apply the scoring and ordering
        queryset = queryset.annotate(relevance=relevance_score)
        
        # Order by relevance (desc), then featured status, then published date
        if search_query:
            return queryset.order_by('-relevance', '-is_featured', '-published_at')
        else:
            return queryset.order_by('-is_featured', '-published_at')
    
    def _extract_search_terms(self, query):
        """Extract and clean search terms from query string"""
        if not query:
            return []
        
        # Remove special characters and split
        clean_query = re.sub(r'[^\w\s]', ' ', query.lower())
        terms = [term.strip() for term in clean_query.split() if len(term.strip()) > 2]
        print(terms)
        
        # Remove common stop words
        stop_words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can',
            'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has',
            'him', 'his', 'how', 'man', 'new', 'now', 'old', 'see', 'two',
            'way', 'who', 'boy', 'did', 'its', 'let', 'put', 'say', 'she',
            'too', 'use', 'job', 'work', 'role', 'position'
        }
        
        return [term for term in terms if term not in stop_words]
    
    def get_search_suggestions(self, query, limit=10):
        """Get search suggestions based on partial query"""
        if not query or len(query) < 2:
            return []
        
        from .models import Job, Skill, Company, JobCategory
        
        suggestions = []
        
        # Job title suggestions
        job_titles = Job.published.filter(
            title__icontains=query
        ).values_list('title', flat=True)[:limit//4]
        
        # Company name suggestions
        company_names = Company.objects.filter(
            name__icontains=query,
            is_verified=True
        ).values_list('name', flat=True)[:limit//4]
        
        # Skill suggestions
        skills = Skill.active.filter(
            name__icontains=query
        ).values_list('name', flat=True)[:limit//4]
        
        # Category suggestions
        categories = JobCategory.active.filter(
            name__icontains=query
        ).values_list('name', flat=True)[:limit//4]
        
        # Combine all suggestions
        suggestions.extend([{'type': 'job_title', 'value': title} for title in job_titles])
        suggestions.extend([{'type': 'company', 'value': name} for name in company_names])
        suggestions.extend([{'type': 'skill', 'value': skill} for skill in skills])
        suggestions.extend([{'type': 'category', 'value': cat} for cat in categories])
        
        return suggestions[:limit]