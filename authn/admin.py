from rest_framework.response import Response
from rest_framework import status
from authn.models import authns
class AdminRequiredMixin:
    def is_admin(self, request):
        student_number = request.user.student_number
        try:
            auth_user = authns.objects.get(student_number=student_number)
            return auth_user.role == 'ADMIN'
        except authns.DoesNotExist:
            return False

    def check_admin_permission(self, request):
        if not self.is_admin(request):
            return Response({"error": "관리자 권한이 필요합니다"}, status=status.HTTP_403_FORBIDDEN)
        return None
