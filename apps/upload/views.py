#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.http import HttpResponse, HttpResponseNotAllowed, HttpResponseServerError
from django.template import RequestContext
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django.contrib.auth.decorators import permission_required
from django.shortcuts import get_object_or_404
from django.db import transaction

from rapidsms.webui.utils import *
from reporters.models import *
from reporters.utils import *


def message(req, msg, link=None):
    return render_to_response(req,
        "message.html", {
            "message": msg,
            "link": link
    })


@permission_required('reporters.can_view')
@require_GET
def main(req):
    return render_to_response(req,
        "upload/index.html", {
    })


@require_http_methods(["GET", "POST"])
def upload(req):
    def get(req):
        return message(req,"GET Gotten!")

    def post(req):
        #req
        added_reporters = parse_csv(req.FILES['csv_file'])
        return message(req, str(added_reporters[0]) + " Reporters Succesfully Uploaded! " + str(added_reporters[1]) + " Duplicates Ignored " + " And " + str(added_reporters[2]) + " New Groups Added. " + str(added_reporters[3]) + " Reporters Were Not Assigned to a Group.")

    # invoke the correct function...
    # this should be abstracted away
    if   req.method == "GET":  return get(req)
    elif req.method == "POST": return post(req)

def parse_csv(csvdata):

    backends = PersistantBackend.objects.all()
    connections = PersistantConnection.objects.all()
    defaultbackend = backends[0]
    groups = ReporterGroup.objects.all()

    reporters_added = 0
    duplicates = 0
    groups = 0
    ungrouped = 0

    for line in csvdata:
        phonedata = line.split(',')
        print phonedata[0]
        print phonedata[1]
        print phonedata[2]
        if len(phonedata) > 3:
            print phonedata[3]
        reporter = Reporter()
        if phonedata[2].strip() == "Contact Detail":
            continue
        if phonedata[2].strip() is "" or (phonedata[0].strip() is "" and phonedata[1].strip() is ""):
            continue
        nametriple = reporter.parse_name(phonedata[0] + " " + phonedata[1])
        reporter.first_name = nametriple[1]
        reporter.last_name = nametriple[2]
        reporter.alias = nametriple[0]
        reporter.save()
            

        connection = PersistantConnection()
        connection.backend = defaultbackend
        connection.identity = "+" + phonedata[2].replace(" ","")
        connection.reporter = reporter
        try:
            connection.save()
            reporters_added += 1
        except:
            # This comes up if there is already a phone number in the system 
            # associated with a person.
            reporter.delete()
            duplicates += 1
            continue

        if len(phonedata) > 3 and phonedata[3].strip() != "":
            #Determine if the group already exists
            filter = {"title" : phonedata[3]}
            existing_groups = ReporterGroup.objects.filter(**filter)
            if len(existing_groups) > 0:
                reporter.groups.add(existing_groups[0])
            else:
                group = ReporterGroup()
                group.title = phonedata[3]
                group.save()
                groups += 1
                reporter.groups.add(group)

            #Either way, save the change
            reporter.save()
        else:
            ungrouped += 1
        
    return [reporters_added,duplicates,groups,ungrouped]
