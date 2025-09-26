class CompanyMediaViewSet(viewsets.ModelViewSet):
    serializer_class = CompanyMediaSerializer
    permission_classes = [IsAuthenticated, IsCompanyOwnerOrAdmin]
    
    def get_queryset(self):
        company_id = self.kwargs.get('company_pk')
        return CompanyMedia.objects.filter(company_id=company_id).order_by('order', '-created_at')
    
    def perform_create(self, serializer):
        company = get_object_or_404(Company, pk=self.kwargs.get('company_pk'))
        serializer.save(company=company, uploaded_by=self.request.user)

class CompanyFollowViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CompanyFollowSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return CompanyFollow.objects.filter(user=self.request.user).select_related('company')

    @action(detail=False, methods=['post'])
    def toggle_notifications(self, request):
        company_id = request.data.get('company_id')
        try:
            follow = CompanyFollow.objects.get(
                company_id=company_id, user=request.user
            )
            follow.notifications_enabled = not follow.notifications_enabled
            follow.save()
            return Response({
                'message': 'Notifications updated',
                'notifications_enabled': follow.notifications_enabled
            })
        except CompanyFollow.DoesNotExist:
            return Response(
                {'error': 'Not following this company'},
                status=status.HTTP_404_NOT_FOUND
            )
            
# @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsJobSeekerUser])
# def follow(self, request, pk=None):
    # company = self.get_object()
    # follow, created = CompanyFollow.objects.get_or_create(
        # company=company, user=request.user,
        # defaults={'notifications_enabled': True}
    # )
    # 
    # if created:
        # Company.objects.filter(pk=company.pk).update(
            # follower_count=F('follower_count') + 1
        # )
        # return Response({'message': 'Following company'}, status=status.HTTP_201_CREATED)
    # return Response({'message': 'Already following'}, status=status.HTTP_200_OK)
# @action(detail=True, methods=['delete'], permission_classes=[IsAuthenticated])
# def unfollow(self, request, pk=None):
    # company = self.get_object()
    # deleted, _ = CompanyFollow.objects.filter(
        # company=company, user=request.user
    # ).delete()
    # 
    # if deleted:
        # Company.objects.filter(pk=company.pk).update(
            # follower_count=F('follower_count') - 1
        # )
        # return Response({'message': 'Unfollowed company'}, status=status.HTTP_200_OK)
    # return Response({'message': 'Not following'}, status=status.HTTP_404_NOT_FOUND)
# @action(detail=True, methods=['get'])
# def followers(self, request, pk=None):
    # company = self.get_object()
    # followers = CompanyFollow.objects.filter(company=company).select_related('user')
    # serializer = CompanyFollowSerializer(followers, many=True)
    # return Response(serializer.data)