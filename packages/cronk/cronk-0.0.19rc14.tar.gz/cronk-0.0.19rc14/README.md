# ========TK_DRAFT=========

# Cronk: a cron-json translator

<!--
The standard commands for the Scorecard and Best Practices badges are:

    [![OpenSSF Scorecard](https://api.securityscorecards.dev/projects/github.com/nebraska-dev/cronk/badge)](https://api.securityscorecards.dev/projects/github.com/nebraska-dev/cronk)
    [![OpenSSF Best Practices](https://bestpractices.coreinfrastructure.org/projects/6829/badge)](https://bestpractices.coreinfrastructure.org/projects/6829)

However, the badges and links always show the project's current scores. In order to
display the correct scores at each blog post, we've therefore used files stored in the
docs/ folder.
-->
[![OpenSSF Scorecard](docs/scorecard_badge.png)](docs/scorecard.json)
[![OpenSSF Best Practices](docs/best_practices_badge.png)](https://htmlpreview.github.io/?https://github.com/nebraska-dev/cronk/blob/main/docs/BadgeApp.html)

---

_This repository is a part of the Google Open Source Blog's_
"[From zero to supply-chain security hero](TK_BLOG_SERIES_URL)" _blog series. It is
meant for demonstrative purposes, and should not be used in production!_

_All information beyond this point is fictional!_

---

- Student: Alice Doe (@nebraska-dev), 2018Q4
- Course: TK_FUNNY_COURSE_NAME_42 @ Cottonwood University (TK Cottonwood is the Nebraska state tree, and there is no such university)

Cronk allows developers to convert files between the crontab and json formats.

To-do:

- Add i18n of periodicity via Babel

## Release to pypi.org

We provide a Dockerfile that sets up the correct environment to publish a new version of Cronk to PyPI.

***These instructions assume the build is executed on a Cloudtop instance.**

### First time Docker setup

Remove any previous Docker installation:

```
sudo apt remove docker-engine
```

Add Google's Docker distribution repository to `apt:

```
glinux-add-repo docker-ce-"$(lsb_release -cs)"
```

Install the Docker runtime:

```
sudo apt update  && sudo apt install docker-ce
```

Check that the Docker daemon is active:

```
systemctl status docker.service
```

The `systemctl` output should look something like this:

```
ltadeut@ltadeut-devbox:~/cronk$ systemctl status docker.service
● docker.service - Docker Application Container Engine
     Loaded: loaded (/usr/lib/systemd/system/docker.service; enabled; preset: enabled)
     Active: active (running) since Tue 2025-09-16 16:29:58 UTC; 1h 54min ago
 Invocation: f59978f5efe2458d904819d125f79a03
TriggeredBy: ● docker.socket
       Docs: https://docs.docker.com
   Main PID: 2421936 (dockerd)
      Tasks: 32
     Memory: 1.2G (peak: 1.2G)
        CPU: 2min 21.072s
     CGroup: /system.slice/docker.service
             └─2421936 /usr/bin/dockerd -H fd:// --containerd=/run/containerd/containerd.sock
```

### Update the cronk version

To release a new version, you must first update the version listed in the `pyproject.toml` file.

Open the `pyproject.toml` file at the root of this repository and edit the `version` field.

### Generate the base image

Run the command below from the repository's root directory:

```
sudo docker build -t release-cronk-to-pypi -f docker/Dockerfile.release_pypi .
```

### Publish to pypi.org

Run the command below to execute the release image (replace `<PYPI_API_TOKEN>` with the value found in https://valentine.corp.google.com/#/show/1757341155550459?tab=metadata):

```
sudo docker run -e TWINE_PASSWORD=<PYPI_API_TOKEN> release-cronk-to-pypi
```
