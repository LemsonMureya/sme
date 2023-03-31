from django.urls import include, path
from . import views
from .views import JobListView, JobCreateView, JobUpdateView, JobDeleteView, DashboardView, JobDetailView

app_name = 'smeApp'

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('jobs/', JobListView.as_view(), name='job_list'),
    path('jobs/add/', JobCreateView.as_view(), name='job_add'),
    path('jobs/edit/<int:pk>/', JobUpdateView.as_view(), name='job_edit'),
    path('jobs/delete/<int:pk>/', JobDeleteView.as_view(), name='job_delete'),
    path('jobs/<int:pk>/', JobDetailView.as_view(), name='job_detail'),

]
