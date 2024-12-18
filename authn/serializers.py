from rest_framework import serializers

# query param 
#class TaskSearchSerializer(serializers.Serializer):
#    offset      = serializers.IntegerField(help_text='기준점 번호', default=0)
#    limit       = serializers.IntegerField(help_text='출력할 row 갯수', default=10)
#    trial_stage = serializers.CharField(help_text='trial_stage param', required=False)
#    department  = serializers.CharField(help_text='department param', required=False)
#    institute 	= serializers.CharField(help_text='institute param', required=False)
#    scope 	= serializers.CharField(help_text='scope param', required=False)
#    title 	= serializers.CharField(help_text='title param', required=False)
#    type 	= serializers.CharField(help_text='type param', required=False)

class LoginSerializer(serializers.Serializer):
    studentNumber   = serializers.CharField(help_text='학번')
    password         = serializers.CharField(help_text='비밀번호')