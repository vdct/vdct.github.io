#!./venv37/bin/python
# -*- coding: utf-8 -*-

import cgi
import cgitb
import json

import db

def get_zone(lat,lon):
    with db.bano_cache.cursor() as cur:
        cur.execute(f"""
                        SELECT ST_AsGeoJSON(ST_Union(geometrie))
                        FROM
                        (SELECT geometrie FROM depts_geo WHERE ST_Contains(geometrie,ST_SetSRID(ST_MakePoint({lon},{lat}),4326))
                        UNION ALL
                        SELECT ST_Transform(ST_Buffer(ST_Transform(ST_SetSRID(ST_MakePoint({lon},{lat}),4326),3857),100000),4326)) a
                     """)
        return((cur.fetchone()[0]))

def get_commune(lat,lon):
    with db.bano_cache.cursor() as cur:
        cur.execute(f"""
                        SELECT p.nom,c.dep
                        FROM polygones_insee p
                        JOIN cog_commune c
                        ON p.insee_com = c.com
                        WHERE ST_Intersects(p.geometrie,ST_Transform(ST_SetSRID(ST_MakePoint({lon},{lat}),4326),3857)) AND
                              c.typecom != 'COMD'
                     """)
        return((cur.fetchone()))

def get_longest_line(lat,lon):
    with db.bano_cache.cursor() as cur:
        cur.execute(f"""
                        WITH
                        zone
                        AS
                        (SELECT ST_Transform(geometrie,3857) as geom_zone FROM depts_geo WHERE ST_Contains(geometrie,ST_SetSRID(ST_MakePoint({lon},{lat}),4326))
                        UNION ALL
                        SELECT ST_Buffer(ST_Transform(ST_SetSRID(ST_MakePoint({lon},{lat}),4326),3857),100000)),
                        centre
                        AS
                        (SELECT ST_Transform(ST_SetSRID(ST_MakePoint({lon},{lat}),4326),3857) as geom_centre),
                        ll
                        AS
                        (SELECT ST_LongestLine(geom_zone,geom_centre) geom_ll
                        FROM centre,zone)
                        SELECT ST_AsGeoJSON(ST_Transform(geom_ll,4326)),ST_Length(geom_ll)
                        FROM ll
                        ORDER BY 2 DESC
                        LIMIT 1
                     """)
        return((cur.fetchone()))                

cgitb.enable()

params = cgi.FieldStorage()
lat = params['lat'].value
lon = params['lon'].value

ll = get_longest_line(lat,lon)

print ("Content-Type: application/json")
print ("")

print(f"[{get_zone(lat,lon)},{json.JSONEncoder().encode(get_commune(lat,lon))},{ll[0]},{ll[1]}]")
