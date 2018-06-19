# vastplace air quality module

This project is a module for the [vastplace](https://github.com/tkerdonc/vastplace) project. It parses csv files storing air quality sensors and gps coordinates.

## Getting Started

### Installing

This install assumes that you already have a vastplace install in ~/src/vastenv/vastplace
We will now create a working copy of this vastplace module, and enable it in vastplace.

```
cd src
git clone https://github.com/tkerdonc/vastplace_air_quality.git
cd vastenv/vastplace/experiments
ln -s ../../../vastplace_air_quality vastplace_air_quality
cd ..
```

This linked the ap_subset module sources to a local folder of vastplace, we now need to enable it :

<pre>
vim centraldb/settings.py
</pre>

and add
<pre>
'experiments.vastplace_air_quality'
</pre>
 to the *INSTALLED_APPS* entry
We also need to route the urls to the ap_subset module :

<pre>
vim centraldb/urls.py
</pre>

and add
<pre>
url(r'^air_quality/', include('experiments.vastplace_air_quality.urls')),
</pre>

to the *urlpatterns* entry.

the ap_subset module should now be enabled.

## Uploading a trace

This module parses csv traces with the following format :

```
YYYY-MM-DDTHH:mm:ss.mmm+00:00,<latitude>,<longitude>,<pm2.5 measurement>
```

Navigate to the following url, and use the trace upload form.
<pre>
/campaignfiles/content
</pre>

Once the trace uploaded, you are prompted with the detail filling form. You must pick the *ambassadair_mobile* or *ambassadair_static* format. Once save, a map will be plotted.
Adding a word starting with '#' in the description will also tag this trace as part of the campaign named by this word.

## Features

This module exposes its features via the following URLs :

|URL                                 | Type |Description                                   |
|------------------------------------|------|----------------------------------------------|
|ambassadair/                        | HTML | Index                                        |
|ambassadair/air_map                 | HTML | Map of all traces                            |
|ambassadair/air_test                | HTML | Geographic cell processing                   |
|ambassadair/bargraph/<targetId_str> | HTML | Air quality bargraph for ids in target_Ids, separated by commas |
|ambassadair/grafana$                | HTML | grafana interfacing function                 |
|ambassadair/grafana/query$          | HTML | grafana interfacing function                 |
|ambassadair/grafana/search$         | HTML | grafana interfacing function                 |
|ambassadair/grafana_sources$        | HTML | grafana interfacing function for datasources |
|ambassadair/grafana_sources/query$  | HTML | grafana interfacing function for datasources |
|ambassadair/grafana_sources/search$ | HTML | grafana interfacing function for datasources |


## License
This project is licensed under the BSD 3 License - see the [LICENSE.md](LICENSE.md) file for details

