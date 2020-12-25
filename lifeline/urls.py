"""lifeline URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from block import views

urlpatterns = [
    path('chain', views.get_chain),
    path('new_transaction', views.new_transaction),
    path('register_new_peers', views.register_new_peers),
    path('register_with_existing_node', views.register_with_existing_node),
    path('pending_tx', views.get_pending_tx),
    path('add_block', views.verify_and_add_block),
    path('mine',views.mine_unconfirmed_transactions),
    path('admin/', admin.site.urls),
]
