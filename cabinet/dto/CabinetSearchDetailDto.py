from rest_framework import serializers

class CabinetSearchDetailDto(serializers.Serializer):
    keyword = serializers.CharField(help_text='검색어')

    def validate_keyword(self, value):
        if value is None:
            raise serializers.ValidationError('검색어를 입력해주세요.')
        elif len(value) == 1 and value.isdigit():
            pass
        elif not isinstance(value, int) and len(value) < 2  :
            raise serializers.ValidationError('검색어는 2글자 이상 입력해주세요.')
        return value