from django.urls import path
from .views import PublicContactView, CandidateInquiryView, AdminInquiryListView, AdminInquiryDetailView, AdminInquiryConvertView

app_name = "inquiries"
urlpatterns = [
    path("public/contact/", PublicContactView.as_view(), name="public-contact"),
    path("candidate/inquiries/", CandidateInquiryView.as_view(), name="candidate-list"),
    path("admin/inquiries/", AdminInquiryListView.as_view(), name="admin-list"),
    path("admin/inquiries/<uuid:inquiry_id>/", AdminInquiryDetailView.as_view(), name="admin-detail"),
    path("admin/inquiries/<uuid:inquiry_id>/convert/", AdminInquiryConvertView.as_view(), name="admin-convert"),
]
