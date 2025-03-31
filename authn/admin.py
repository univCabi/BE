from rest_framework.response import Response
from rest_framework import status, permissions
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

class IsAdmin(permissions.BasePermission):
    """
    관리자 권한이 있는 사용자만 접근을 허용하는 커스텀 권한 클래스
    """
    message = "관리자 권한이 필요합니다"  # 권한 거부 시 표시될 메시지

    def has_permission(self, request, view):
        # 인증되지 않은 사용자는 바로 거부
        if not request.user or not request.user.is_authenticated:
            return False
        
        # 학번으로 role 확인
        try:
            auth_user = authns.objects.get(student_number=request.user.student_number)
            return auth_user.role == 'ADMIN'
        except authns.DoesNotExist:
            return False