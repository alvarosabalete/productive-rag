"""Capa de acceso a servicios AWS (simulados en LocalStack).

Aísla el uso de boto3 del resto de la app. boto3 es síncrono: usar solo en
procesos aparte (script de ingesta) o en el arranque de la app, nunca dentro de
rutas async.
"""
