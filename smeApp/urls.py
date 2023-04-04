from django.urls import include, path
from . import views
from .views import(JobListView,
                    JobCreateView,
                    JobUpdateView,
                    JobDeleteView,
                    DashboardView,
                    JobDetailView,
                    IncomeUpdateView,
                    ExpenseUpdateView,
                    IncomeDeleteView,
                    ExpenseDeleteView,
                    TransactionsView,
                    ExpensesDataView,
                    ClientsListView,
                    ClientsList,
                    CompanyProfileCreateView)

app_name = 'smeApp'

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('create_company_profile/', CompanyProfileCreateView.as_view(), name='create_company_profile'),
    path('jobs/', JobListView.as_view(), name='job_list'),
    path('jobs/add/', JobCreateView.as_view(), name='job_add'),
    path('jobs/edit/<int:pk>/', JobUpdateView.as_view(), name='job_edit'),
    path('jobs/delete/<int:pk>/', JobDeleteView.as_view(), name='job_delete'),
    path('jobs/<int:pk>/', JobDetailView.as_view(), name='job_detail'),
    path('client/create/', views.client_create, name='client_create'),
    path('clients_list/', ClientsListView.as_view(), name='clients_list'),
    path('clients/', ClientsList.as_view(), name='client_list'),
    path('add_expense/', views.AddExpenseView.as_view(), name='add_expense'),
    path('add_income/', views.AddIncomeView.as_view(), name='add_income'),
    path('transactions/', views.TransactionsView.as_view(), name='transactions'),
    path('income/update/<int:pk>/', IncomeUpdateView.as_view(), name='income-update'),
    path('expense/update/<int:pk>/', ExpenseUpdateView.as_view(), name='expense-update'),
    path('income/delete/<int:pk>/', IncomeDeleteView.as_view(), name='income-delete'),
    path('expense/delete/<int:pk>/', ExpenseDeleteView.as_view(), name='expense-delete'),
    path('expenses_data/', ExpensesDataView.as_view(), name='expenses_data'),
    path('profit_loss_data/', views.ProfitLossDataView.as_view(), name='profit_loss_data'),
    path('create_invoice/', views.CreateInvoiceView.as_view(), name='create_invoice'),
    path('view_invoice/<int:invoice_id>/', views.ViewInvoiceView.as_view(), name='view_invoice'),
    path('generate_pdf/<int:invoice_id>/', views.GeneratePDFView.as_view(), name='generate_pdf'),
    path('preview_pdf/<int:invoice_id>/', views.PreviewPDFView.as_view(), name='preview_pdf'),

]
