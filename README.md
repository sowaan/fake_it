## Fake It

App to convert real live data of SowaanERP to fake demo data

### Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app https://github.com/sowaan/fake_it --branch main
bench --site [your.site.name] install-app fake_it
bench pip install -e apps/fake_it
bench --site [your.site.name] migrate

#### License

mit
