from django.db.models import Q, F, Value, Case, When, IntegerField
from django.utils import timezone
from datetime import timedelta
import re

class JobSearchEngine:
    """Advanced job search with relevance scoring"""
    
    def search(self, search_params, base_queryset=None):
        """
        Perform advanced job search with relevance scoring
        """
        if base_queryset is None:
            from .models import Job
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
    
    def _apply_filters(self, queryset, params):
        """Apply various filters to the queryset"""
        
        # Location filter
        location = params.get('location')
        remote_only = params.get('remote_only')
        
        if remote_only:
            queryset = queryset.filter(remote_allowed=True)
        elif location:
            queryset = queryset.filter(
                Q(location__icontains=location) | Q(remote_allowed=True)
            )
        
        # Job type filter
        job_types = params.get('job_type')
        if job_types:
            queryset = queryset.filter(job_type__in=job_types)
        
        # Experience level filter
        experience_levels = params.get('experience_level')
        if experience_levels:
            queryset = queryset.filter(experience_level__in=experience_levels)
        
        # Category filter
        category = params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        # Industry filter
        industry = params.get('industry')
        if industry:
            queryset = queryset.filter(industry=industry)
        
        # Company filter
        company = params.get('company')
        if company:
            queryset = queryset.filter(company=company)
        
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
            queryset = queryset.filter(skills__in=skills)
        
        # Featured filter
        is_featured = params.get('is_featured')
        if is_featured is not None:
            queryset = queryset.filter(is_featured=is_featured)
        
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