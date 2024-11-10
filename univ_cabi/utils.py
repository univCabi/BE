from rest_framework import serializers

class CamelCaseSerializer(serializers.Serializer):
    def to_camel_case(self, snake_str):
        components = snake_str.split('_')
        return components[0] + ''.join(x.title() for x in components[1:])
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        return {self.to_camel_case(key): value for key, value in data.items()}