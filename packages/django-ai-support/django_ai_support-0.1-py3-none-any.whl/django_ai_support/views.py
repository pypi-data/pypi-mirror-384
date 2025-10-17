from rest_framework.views import APIView
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema

from .serializers import InputOutputChatSerializer
from .backends import normal_chat_with_ai

class ChatAiSupportApi(APIView):

    @extend_schema(
        tags=["Django AI Support"],
        request=InputOutputChatSerializer,
        responses=InputOutputChatSerializer
    )
    def post(self, request):
        
        serializer = InputOutputChatSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ai_response = normal_chat_with_ai(serializer.validated_data["message"],
                                          session_id=request.session.session_key)
        
        return Response(InputOutputChatSerializer({"message": ai_response}).data)


