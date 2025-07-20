from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super(CustomTokenObtainPairSerializer, cls).get_token(user)

        token['username'] = user.username
        token['email'] = user.email

        if hasattr(user, 'profile'):
            token['profile_id'] = str(user.profile.id)

        return token
