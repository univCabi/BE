from user.persistence.user_repository import UserRepository

user_repository = UserRepository()

class UserService :
    def get_user_by_student_number(self, student_number) :
        return user_repository.get_user_by_student_number(student_number)
    
    def update_user_is_visible_by_student_number(self, student_number, is_visible) :
        return user_repository.update_user_is_visible_by_student_number(student_number, is_visible)