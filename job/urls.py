from django.urls import path
from . import views

urlpatterns = [
    # ... existing urls ...
    path('salary_prediction/', views.salary_prediction_page, name='salary_prediction'),
    path('predict_salary/', views.predict_salary, name='predict_salary'),
    path('get_model_info/', views.get_model_info, name='get_model_info'),
    path('get_available_models/', views.get_available_models, name='get_available_models'),
    path('train_salary_model/', views.train_salary_model, name='train_salary_model'),
    # ... existing urls ...
] 