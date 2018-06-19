# Create your views here.
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import HttpResponse
from django.http import HttpResponseNotFound
from django.http import HttpResponseRedirect

from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view

import base64
from bson.objectid import ObjectId
from datetime import datetime
from gridfs import GridFS
import json
import numpy as np
import os

from storage import database
from centraldb.decorators import cached_call
from mapper.utils import osm_latlon_to_tile_number, osm_tile_number_to_latlon
from mapper.cell_utils import getMergedCells
from mapper.utils import pointStyle
from plotting.utils import plotBarGraph, plotCDF

def index(request):
    return air_map(request)

@cached_call
def air_map_get_points_bysource(srcId):
	retval = []
	client = database.getClient()
	point_collection = client.point_database.sensors.find({'sourceId':ObjectId(srcId)})
	GPS = (-1,-1)
	for point in point_collection:
		if point['sensorType'] == 'GPS':
			GPS = point['sensorValue']
		elif point['sensorType'] == 'PM2.5':
			if GPS != (-1, -1):
				retval.append(GPS + [point['sensorValue']])
	client.close()
	return retval

def air_map(request):
	tiling_level = 17
	response = None
	client = database.getClient()
	db = client.trace_database
	fs = GridFS(db)
	responseData = {'trajectories':[], 'points':[], 'rectangles':[]}
	tiledMeasures = {}
	for traceFile in fs.find():
		if 'sourceTypes' in traceFile.metadata and ( "ambassadair_mobile" in traceFile.metadata['sourceTypes'] or "ambassadair_static" in traceFile.metadata['sourceTypes']):
			points = air_map_get_points_bysource(traceFile._id)
			responseData['trajectories'].append({'points': [[lon, lat] for lat, lon, _ in points], 'id':traceFile._id})
			for lat, lon, val in points:
				tile_number = osm_latlon_to_tile_number(lon, lat, tiling_level)
				if tile_number not in tiledMeasures:
					tiledMeasures[tile_number] = []
				tiledMeasures[tile_number].append(val)

	for tileX, tileY in tiledMeasures:
		x1, y1 = osm_tile_number_to_latlon(tileX, tileY, tiling_level)
		x2, y2 = osm_tile_number_to_latlon(tileX + 1, tileY + 1, tiling_level)
		mean = np.mean(tiledMeasures[tileX, tileY])
		mean_str = "%.3f" % mean
		if mean > 10:
            		color = 'rgba(255, 0, 0, 0.3)'
		else:
            		color = 'rgba(0, 255, 0, 0.3)'
		responseData['rectangles'].append((x1, x2, y1, y2, mean_str, color))

	client.close()
        return render(request, 'mapper/map.html', responseData)



def air_test(request):
    osm_zoom = 17


    responseData = {'trajectories':[], 'points':[]}
    responseData['point_styles'] = []

    pm2point5_cells = getMergedCells('ambassadair_mobile', 'PM2.5', osm_zoom)

    for u in pm2point5_cells:
        gps, average = u
        color = intToGreenRedColor(average, 0, 25)
        responseData['point_styles'].append(pointStyle(color[1:], color, 3))
    	responseData['points'] +=  [{'lonlat':[gps[-1], gps[0]], 'style':color[1:]}]

    responseData['trajectories'].append({'points': [[u[0][1], u[0][0]], [u[0][-1], u[0][0]]]})

    return render(request, 'mapper/map.html', responseData)

def intToGreenRedColor(pInt, minValue, maxValue):
    """ Red means value equals to max, green, equals to min"""
    if pInt < minValue:
        pInt = minValue
    if pInt > maxValue:
        pInt = maxValue

    ratio = int(float(pInt - minValue) / (maxValue - minValue)  * 255)

    red_hex = hex(ratio)
    green_hex = hex(255 - ratio)


    red_str = str(red_hex)[2:]
    if len(red_str) == 1:
        red_str = "0" + red_str
    green_str = str(green_hex)[2:]
    if len(green_str) == 1:
        green_str = "0" + green_str

    retval = "#%s%s00" % (red_str, green_str)

    return retval

@api_view(['GET'])
def grafana (request):
    """ Only used to test datasource, always return 200 OK"""
    responseData = {}
    return Response(responseData, status=status.HTTP_200_OK)

@api_view(['POST'])
def grafana_search(request):
    responseData = {}
    return Response(responseData, status=status.HTTP_200_OK)

@api_view(['POST'])
def grafana_query(request):
    """ dispatcher function for all grafana queries (except sources) dispatch depending on targets field"""
    request_dict = json.loads(request.body)

    target = request_dict['targets'][0]['target'].split('.')
    if len(target) <= 1:
        responseData = grafana_query_timeseries_impl(request_dict)
    elif target[1].endswith('median'):
        responseData =grafana_query_median_impl(request)
    elif target[1].startswith('split'):

        split_value = float(target[1].split('=')[1])
        request_dict['targets'][0]['target'] = target[0]
        responseData = grafana_query_splitted_timeseries_impl(request_dict, split_value)

    return Response(responseData, status=status.HTTP_200_OK)

def grafana_query_timeseries_impl(request_dict):
    responseData = [
        {"target":request_dict['targets'],
        "datapoints":[
            ]
        }
    ]

    target_ids = request_dict['targets'][0]['target'].lstrip('(').rstrip(')').split('|')

    from_dt = datetime.strptime(request_dict["range"]["from"], '%Y-%m-%dT%H:%M:%S.%fZ')
    to_dt = datetime.strptime(request_dict["range"]["to"], '%Y-%m-%dT%H:%M:%S.%fZ')

    from_ts = float(from_dt.strftime('%s'))
    to_ts = float(to_dt.strftime('%s'))

    client = database.getClient()
    db = client.trace_database
    fs = GridFS(db)
    for traceFile in fs.find({'_id':{'$in':[ObjectId(u) for u in target_ids]}}):
	point_collection = client.point_database.sensors.find({'sourceId':ObjectId(traceFile._id), 'sensorType': 'PM2.5', 'vTimestamp':{'$gt':from_ts, '$lt':to_ts}})
        for point in point_collection:
            responseData[0]["datapoints"].append([ point["sensorValue"] , int(point["vTimestamp"] * 1000)])

    return responseData

def grafana_query_splitted_timeseries_impl(request_dict, splitted_value):
    unsplitted_response = grafana_query_timeseries_impl(request_dict)

    under_key = "<=" + str(splitted_value)
    over_key = ">" + str(splitted_value)

    #Temporarily use a dict for responseData, will return only the values
    responseData = {
        under_key:{"target":under_key,
        "datapoints":[
            ]
        },
        over_key:{"target":over_key,
        "datapoints":[
            ]
        },
    }

    for point in unsplitted_response[0]["datapoints"]:
        if point[0] <= splitted_value:
            responseData[under_key]['datapoints'].append(point)
        else:
            responseData[over_key]['datapoints'].append(point)

    return responseData.values()

def grafana_query_median_impl(request):
    request_dict = json.loads(request.body)
    responseData = [
        {"target":request_dict['targets'],
        "datapoints":[
            ]
        }
    ]
    values = []

    target_ids = request_dict['targets'][0]['target'][:-len('.median')].lstrip('(').rstrip(')').split('|')

    from_dt = datetime.strptime(request_dict["range"]["from"], '%Y-%m-%dT%H:%M:%S.%fZ')
    to_dt = datetime.strptime(request_dict["range"]["to"], '%Y-%m-%dT%H:%M:%S.%fZ')

    from_ts = float(from_dt.strftime('%s'))
    to_ts = float(to_dt.strftime('%s'))

    client = database.getClient()
    db = client.trace_database
    fs = GridFS(db)
    for traceFile in fs.find({'_id':{'$in':[ObjectId(u) for u in target_ids]}}):
        point_collection = client.point_database.sensors.find({'sourceId':ObjectId(traceFile._id), 'sensorType': 'PM2.5', 'vTimestamp':{'$gt':from_ts, '$lt':to_ts}})
        for point in point_collection:
            values.append(int(point["sensorValue"]))

    responseData[0]["datapoints"].append([ np.median(values), float(from_ts + to_ts)  / 2])
    return responseData

@api_view(['POST'])
def grafana_sources(request):
    request_dict = json.loads(request.body)

@api_view(['POST'])
def grafana_sources_query(request):
    request_dict = json.loads(request.body)

@api_view(['POST'])
def grafana_sources_search(request, format=None):
    request_dict = json.loads(request.body)

    source_type = None

    if request_dict['target'] == "mobile_ids":
        source_type = "ambassadair_mobile"
    elif request_dict['target'] == "static_ids":
        source_type = "ambassadair_static"

    client = database.getClient()
    db = client.trace_database
    fs = GridFS(db)
    responseData = []
    for traceFile in fs.find():
	if 'sourceTypes' in traceFile.metadata and source_type in traceFile.metadata['sourceTypes']:
	    responseData.append({
                        "text":traceFile.filename,
                        "value":str(traceFile._id)
                    }
            )

    return Response(responseData, status=status.HTTP_200_OK)

def bargraph(request, targetId_str):

    bins_lower_keys = [0, 14, 21, 28, 35, 60]

    # Not all bins are the same size, adjust the widths
    widths = [bins_lower_keys[i+1] - bins_lower_keys[i] for i in range(len(bins_lower_keys) - 1)]
    widths.append(widths[-1])

    x_labels = [str(bins_lower_keys[i]) + ' - ' + str(bins_lower_keys[i+1]) for i in range(len(bins_lower_keys) - 1)]
    x_labels.append('>' + str(bins_lower_keys[-1]))

    #matplotlib would center around the lower key, add some offsets depending on the withs
    bins_Xs = []
    for bInd, bin_lower in enumerate(bins_lower_keys):
        bins_Xs.append(bin_lower + 0.5 * widths[bInd])

    barData = {k:0 for k in bins_lower_keys}

    target_ids = targetId_str.split(',')

    client = database.getClient()
    db = client.trace_database
    fs = GridFS(db)

    for traceFile in fs.find({'_id':{'$in':[ObjectId(u) for u in target_ids]}}):
        point_collection = client.point_database.sensors.find({'sourceId':ObjectId(traceFile._id), 'sensorType': 'PM2.5'})
        for point in point_collection:
            bin_key = max([k for k in bins_lower_keys if k <= point['sensorValue']])
            barData[bin_key] += 1

    buf = plotBarGraph(
        [{
            'X':bins_Xs,
            'Y':[barData[k] for k in sorted(barData.keys())],
            'label' : "PM2.5",
            'width' : widths,
            'color' : 'green'
        }],
        xlabel = 'PM2.5',
        ylabel = 'Occurence',
        x_ticks = bins_Xs,
        x_tick_labels = x_labels,
        legend = True
    )

    return HttpResponse(buf, content_type='image/svg+xml')
