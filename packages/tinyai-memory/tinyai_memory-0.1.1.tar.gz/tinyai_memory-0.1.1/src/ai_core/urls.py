from django.urls import path
from .views import learn_view, ask_view, attend_view, reflect_view,knowledge_view,compose_view, chain_reasoning_view

urlpatterns = [
    path("learn/", learn_view),
    path("ask/", ask_view),
    path("attend/", attend_view),
    path("reflect/", reflect_view),
    path("knowledge/",knowledge_view),
    path("compose/",compose_view),
    path("chain_reasoning/",chain_reasoning_view),
]
