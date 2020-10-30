from django.contrib.auth.models import User, Group
from rest_framework import serializers

from .models import Log


class UserSerializer(serializers.HyperlinkedModelSerializer):
    logs = serializers.PrimaryKeyRelatedField(many=True, queryset=Log.objects.all())
    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'groups', 'logs']


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ['url', 'name']


class LogSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        model = Log
        fields = ['url', 'log_id', 'log_status', 'log_message', 'owner', 'last_modified']