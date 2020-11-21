from waitress import serve
import flaskstuff
serve(flaskstuff.app,host='192.168.0.112',port=8080)