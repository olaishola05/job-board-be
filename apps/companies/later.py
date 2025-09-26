# tasks for company-related operations
@shared_task
def send_company_notifications():
    """Send notifications to followers about new jobs"""
    
    yesterday = timezone.now() - timedelta(days=1)
    new_jobs = Job.published.filter(published_at__gte=yesterday).select_related('company')
    
    for job in new_jobs:
        # Get followers who want notifications
        followers = CompanyFollow.objects.filter(
            company=job.company,
            notifications_enabled=True
        ).select_related('user')
        
        for follow in followers:
            send_job_notification_email.delay(
                user_id=follow.user.user,
                job_id=job.id
            )
            
@shared_task
def update_company_ratings():
    """Update company ratings based on reviews"""
    
    companies_with_reviews = Company.objects.annotate(
        review_count=Count('reviews')
    ).filter(review_count__gt=0)
    
    for company in companies_with_reviews:
        rating_data = company.reviews.aggregate(
            avg_rating=Avg('rating'),
            count=Count('id')
        )
        company.rating = rating_data['avg_rating']
        company.review_count = rating_data['count']
        company.save(update_fields=['rating', 'review_count'])
# signal

@receiver(post_save, sender=CompanyFollow)
def update_follower_count_on_follow(sender, instance, created, **kwargs):
    """Update company follower count when followed"""
    if created:
        Company.objects.filter(pk=instance.company.pk).update(
            follower_count=F('follower_count') + 1
        )

@receiver(post_delete, sender=CompanyFollow)
def update_follower_count_on_unfollow(sender, instance, **kwargs):
    """Update company follower count when unfollowed"""
    Company.objects.filter(pk=instance.company.pk).update(
        follower_count=F('follower_count') - 1
    )

@receiver(post_save, sender=CompanyReview)
def update_company_rating_on_review(sender, instance, created, **kwargs):
    """Update company rating when review is added/updated"""
    if created or not created:
        update_company_ratings.delay()

@receiver(post_delete, sender=CompanyReview)
def update_company_rating_on_review_delete(sender, instance, **kwargs):
    """Update company rating when review is deleted"""
    update_company_ratings.delay()

company_verified = Signal()
company_featured = Signal()


@receiver(company_verified)
def handle_company_verification(sender, company, verified_by, **kwargs):
    """Handle company verification event"""
    AuditLog.log_action(
        user=verified_by,
        action='verify_company',
        obj=company,
        details={
            'company_name': company.name,
            'verified_by': verified_by.get_full_name() if verified_by else 'System'
            'verification_date': company.updated_at.isoformat(),
        }
    )


@receiver(company_featured)
def handle_company_featured(sender, company, featured_by, **kwargs):
    """Handle company featured event"""
    AuditLog.log_action(
        user=featured_by,
        action='feature_company',
        obj=company,
        details={
            'company_name': company.name,
            'featured_by': featured_by.get_full_name() if featured_by else 'System'
            'featured_date': company.updated_at.isoformat(),
        }
    )
# views.py
@action(detail=True, methods=['get', 'post'])
def reviews(self, request, pk=None):
    company = self.get_object()
    
    if request.method == 'GET':
        reviews = company.reviews.select_related('user').order_by('-created_at')
        page = self.paginate_queryset(reviews)
        serializer = CompanyReviewSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)
    
    elif request.method == 'POST':
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, 
                          status=status.HTTP_401_UNAUTHORIZED)
        
        if CompanyReview.objects.filter(company=company, user=request.user).exists():
            return Response({'error': 'You have already reviewed this company'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        serializer = CompanyReviewCreateSerializer(data=request.data)
        if serializer.is_valid():
            review = serializer.save(company=company, user=request.user)
            
            self._update_company_rating(company)
            
            response_serializer = CompanyReviewSerializer(
                review, context={'request': request}
            )
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
      
    # Tests
    
    # def test_company_follow(self):
    # self.client.force_authenticate(user=self.user)
    # url = reverse('companies:company-follow', kwargs={'pk': self.company.id})
    # response = self.client.post(url)
    # self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    # self.assertTrue(
        # CompanyFollow.objects.filter(company=self.company, user=self.user).exists()
    # )
# def test_company_follow_duplicate(self):
    # CompanyFollow.objects.create(company=self.company, user=self.user)
    # self.client.force_authenticate(user=self.user)
    # url = reverse('companies:company-follow', kwargs={'pk': self.company.id})
    # response = self.client.post(url)
    # self.assertEqual(response.status_code, status.HTTP_200_OK)
# def test_company_unfollow(self):
    # CompanyFollow.objects.create(company=self.company, user=self.user)
    # self.client.force_authenticate(user=self.user)
    # url = reverse('companies:company-unfollow', kwargs={'pk': self.company.id})
    # response = self.client.delete(url)
    # self.assertEqual(response.status_code, status.HTTP_200_OK)
    # self.assertFalse(
        # CompanyFollow.objects.filter(company=self.company, user=self.user).exists()
    # )
# def test_company_reviews_get(self):
    # CompanyReview.objects.create(
        # company=self.company, user=self.user,
        # rating=5, title='Great company',
        # content='Really enjoyed working here'
    # )
    # self.client.force_authenticate(user=self.user)
    # url = reverse('companies:company-reviews', kwargs={'pk': self.company.id})
    # response = self.client.get(url)
    # self.assertEqual(response.status_code, status.HTTP_200_OK)
    # self.assertEqual(len(response.data['results']), 1)
# def test_company_reviews_post(self):
    # self.client.force_authenticate(user=self.user)
    # data = {
        # 'rating': 4,
        # 'title': 'Good company',
        # 'content': 'Nice place to work',
        # 'pros': 'Good culture',
        # 'cons': 'Long hours'
    # }
    # url = reverse('companies:company-reviews', kwargs={'pk': self.company.id})
    # response = self.client.post(url, data)
    # self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    # self.assertEqual(CompanyReview.objects.count(), 1)
# def test_company_reviews_duplicate_forbidden(self):
    # CompanyReview.objects.create(
        # company=self.company, user=self.user,
        # rating=5, title='Great', content='Great company'
    # )
    # self.client.force_authenticate(user=self.user)
    # data = {
        # 'rating': 3,
        # 'title': 'Another review',
        # 'content': 'Different opinion'
    # }
    # url = reverse('companies:company-reviews', kwargs={'pk': self.company.id})
    # response = self.client.post(url, data)
    # self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)