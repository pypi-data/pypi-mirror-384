from rest_framework import serializers

class InputOutputChatSerializer(serializers.Serializer):
    message = serializers.CharField()

