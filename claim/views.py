import base64
from django.conf import settings
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.http import HttpResponse
from report.services import ReportService
from .services import ClaimReportService
from .reports import claim
from .apps import ClaimConfig
from .models import ClaimAttachment
from django.utils.translation import gettext as _
import core


def print(request):
    if not request.user.has_perms(ClaimConfig.claim_print_perms):
        raise PermissionDenied(_("unauthorized"))
    report_service = ReportService(request.user)
    report_data_service = ClaimReportService(request.user)
    data = report_data_service.fetch(request.GET['uuid'])
    return report_service.process('claim_claim', data, claim.template)


def attach(request):
    queryset = ClaimAttachment.objects.filter(*core.filter_validity())
    if settings.ROW_SECURITY:
        from location.schema import userDistricts
        dist = userDistricts(request.user._u)
        queryset = queryset.select_related("claim")\
            .filter(
            claim__health_facility__location__id__in=[
                l.location.id for l in dist]
        )
    attachment = queryset\
        .filter(id=request.GET['id'])\
        .first()
    if not attachment:
        raise PermissionDenied(_("unauthorized"))
    if attachment.document is None:
        response = HttpResponse(status=404)
        return response
    response = HttpResponse(content_type=("application/x-binary" if attachment.mime is None else attachment.mime))
    response['Content-Disposition'] = 'attachment; filename=%s' % attachment.filename
    response.write(base64.b64decode(attachment.document))
    return response
