**Step 1:** Clone the repo

```
$ git clone https://github.com/frappe/lms.git

$ cd lms

$ cd docker
```

**Step 2:** Run docker-compose

```
$ docker-compose up
```

**Step 3:** Visit the website at http://localhost:8000/

You'll have to go through the setup wizard to setup the website for the first time you access it. Login using the following credentiasl to complete the setup wizard.

```
Username: Administrator
password: admin
```

TODO: Explain how to load sample data

## Restore shared LMS data

If your team has committed a shared database dump at `docker/lms_sync_db.sql.gz`, you can restore it after the default site finishes booting.

**Step 1:** Start Docker and wait for the site initialization to finish

```bash
cd docker
docker compose up -d
```

Wait a few minutes for `init.sh` to finish creating the blank `lms.localhost` site.

**Step 2:** Open the `frappe` container

```bash
docker compose exec frappe bash
```

**Step 3:** Restore the shared dump

```bash
cd frappe-bench
bench --site lms.localhost restore /workspace/lms_sync_db.sql.gz --mariadb-root-password 123
```

**Step 4:** Apply migrations and clear cache

```bash
bench --site lms.localhost migrate
bench --site lms.localhost clear-cache
exit
```

After restore, members who clone the repository will see the same shared course and certificate data that was exported into `lms_sync_db.sql.gz`.

## Stopping the server

Press `ctrl+c` in the terminal to stop the server. You can also run `docker-compose down` in another terminal to stop it.

To completely reset the instance, do the following:

```
$ docker-compose down --volumes
$ docker-compose up
```
