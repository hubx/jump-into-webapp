from flask import Flask, url_for, redirect
import subprocess
import random

from celery_task import make_celery

app = Flask("webapp")
app.config.update(
    CELERY_BROKER_URL = 'sqla+sqlite:///celerydb.sqlite',
    CELERY_RESULT_BACKEND = 'db+sqlite:///results.sqlite'
)
celery = make_celery(app)

@app.route('/<user>/<repository>')
def github(user, repository):
	result = live_instace.delay(user, repository)
	return redirect(url_for('status_for', id=result.id))

@app.route('/status/<id>')
def status_for(id):
	r = live_instace.AsyncResult(id)
	if r.ready():
		return redirect('http://localhost:5000/static/noVNC/vnc.html?autoconnect=true&host=localhost&password=1234&path=&port='+
			str(r.get()))
	else:
		return '<script>setTimeout(function(){window.location.reload(1);}, 10000);</script>booting up'

@celery.task(track_started=True)
def live_instace(user, repository):
	#xx check if repository exists
	commit = build_image(user, repository)
	return run_image(user, repository, commit)

def build_image(user, repository, commit="HEAD"):
	project = "%s/%s" % (user, repository)
	#xx check if commit already has been built
	#sudo docker.io images | grep hubx/swa-battack | grep head
	try:
		subprocess.check_call(["sudo", "docker.io", "build", "-t", project.lower() + ":" + commit, 
								"https://github.com/" + project + ".git"])
	except subprocess.CalledProcessError as e:
		print "[ERROR] Could not build image: " + str(e)

	return commit

def run_image(user, repository, commit):
	project = "%s/%s" % (user, repository)
	#xx choose free instance name
	instance = user + "-" + repository + "-" + str(random.randint(1, 100)) + "-" + commit

	#xx choose free port
	port = str(random.randint(5900, 15900))
	try:
		subprocess.check_call([	"sudo", "docker.io", "run", "-d", 
								"--name", instance,
								"-p", port+":80",
								project.lower() + ":" + commit])
		print port
	except subprocess.CalledProcessError as e:
		print "[ERROR] Could not start image: " + str(e)

	return port

# xx delete container

if __name__ == '__main__':
	with app.test_request_context():
		print url_for('github', user='hubx', repository='SWA-BAttack')
	app.run(debug=True)

