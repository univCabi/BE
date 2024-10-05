from rest_framework import serializers

# query param 
class TaskSearchSerializer(serializers.Serializer):
    offset      = serializers.IntegerField(help_text='기준점 번호', default=0)
    limit       = serializers.IntegerField(help_text='출력할 row 갯수', default=10)
    trial_stage = serializers.CharField(help_text='trial_stage param', required=False)
    department  = serializers.CharField(help_text='department param', required=False)
    institute 	= serializers.CharField(help_text='institute param', required=False)
    scope 	= serializers.CharField(help_text='scope param', required=False)
    title 	= serializers.CharField(help_text='title param', required=False)
    type 	= serializers.CharField(help_text='type param', required=False)

class TaskPostSerializer(serializers.Serializer):
    number           = serializers.CharField(help_text='프로젝트 번호')
    title            = serializers.CharField(help_text='프로젝트 제목')
    duration         = serializers.CharField(help_text='연구 기간')
    number_of_target = serializers.CharField(help_text='연구 번호')
    department       = serializers.CharField(help_text='의학 부서')
    institute        = serializers.CharField(help_text='연구 기관')
    type             = serializers.CharField(help_text='연구 형태')
    trialStage       = serializers.CharField(help_text='시행단계')
    scope            = serializers.CharField(help_text='연구 기관 범위')