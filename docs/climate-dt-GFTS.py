import os
import earthkit.data
import earthkit.maps
import earthkit.regrid
from polytope import api
import s3fs
import datetime
import calendar

def retrieve(param, model, date, levtype, levelist=None, times="0000"):
    # This request matches multiple parameter of the climate DT
    request = {
        "class": "d1",
        "dataset": "climate-dt",
        "activity": "ScenarioMIP",
        "experiment": "SSP3-7.0",
        "realization": "1",
        "generation" : "1",
        "model": model,
        "resolution": "high",
        "expver": "0001",
        "stream": "clte",
        "date": date,
        "time": times,
        "type": "fc",
        "levtype": levtype,
        "param": param
    }
    if levelist is not None:
        request["levelist"]=levelist

    print(request)
    #data is an earthkit streaming object but with stream=False will download data immediately 
    data = earthkit.data.from_source("polytope", "destination-earth", request, address="polytope.lumi.apps.dte.destination-earth.eu", stream=False)
    return data


s3 = s3fs.S3FileSystem(
    anon=False,
    profile="gfts",
    client_kwargs={
        "endpoint_url": "https://s3.gra.perf.cloud.ovh.net",
        "region_name": "gra",
    },
)

# Get lsm
# if not os.path.isfile("lsm.grib"):
#    data = retrieve(param=172, model="ifs-nemo", date="20200101", levtype="sfc")
#    data.save("lsm.grib")


years = [2021, 2022, 2023, 2024]
months = [6]
models = ["ifs-nemo", "icon"]
maxlevels = {}
maxlevels["ifs-nemo"] = 75
maxlevels["icon"] = 72
shortname = {}
# o3d
shortname["263501"] = "avg_thetao"
shortname["263500"] = "avg_so"
shortname["263505"] = "avg_von"
shortname["263506"] = "avg_uoe"
shortname["263507"] = "avg_wo"
# o2d
shortname["263100"] = "avg_sos"
shortname["263101"] = "avg_tos"
shortname["263121"] = "avg_hc300m"
shortname["263122"] = "avg_hc700m"
shortname["263124"] = "avg_zos"

# sfc
#shortname["172"] = "lsm" # available at time=0000 only
shortname["146"] = "sshf"
shortname["147"] = "slhf"

levtype = {}
# o3d
levtype["263501"] = "o3d"
levtype["263500"] = "o3d"
levtype["263505"] = "o3d"
levtype["263506"] = "o3d"
levtype["263507"] = "o3d"
# o2d
levtype["263100"] = "o2d"
levtype["263101"] = "o2d"
levtype["263121"] = "o2d"
levtype["263122"] = "o2d"
levtype["263124"] = "o2d"
# sfc
levtype["172"] = "sfc" # available at time=0000 only
levtype["146"] = "sfc"
levtype["147"] = "sfc"

times = '0000/0100/0200/0300/0400/0500/0600/0700/0800/0900/1000/1100/1200'

for model in models:
    for param in shortname.keys():
        for year in years:
            for month in months:
                start_date = datetime.date(year, month, 1).strftime("%Y%m%d")
                mid_date = datetime.date(year, month, 15).strftime("%Y%m%d")
                mid_date1 = datetime.date(year, month, 16).strftime("%Y%m%d")
                _, number_of_days = calendar.monthrange(year, month)
                end_date = datetime.date(year, month, number_of_days).strftime("%Y%m%d")
                levelist = "1/to/" + str(maxlevels[model])
                
                outfile = shortname[param] + "_" + model + "_" + start_date + "-" + mid_date + ".grib"
                #print("rclone " + outfile + " gfts:gfts-reference-data/ClimateDT/" + outfile)
                if os.path.isfile(outfile): 
                    #s3.ls("gfts-reference-data/ClimateDT/raw/" + outfile)
                    print(outfile, " already exists")
                else:
                    print("retrieve ", outfile)
                    data = retrieve(param=param, model=model, date=start_date + "/to/" + mid_date, levtype=levtype[param], levelist=levelist)
                    data.save(outfile)
                    cmd = "rclone copy " + outfile + " gfts:gfts-reference-data/ClimateDT/raw/"
                    os.system(cmd) 
                    os.remove(outfile)
                    os.system("touch " + outfile) 

                outfile = shortname[param] + "_" + model + "_" + mid_date1 + "-" + end_date + ".grib"

                #print("rclone " + outfile + " gfts:gfts-reference-data/ClimateDT/" + outfile)
                if os.path.isfile(outfile): 
                    #s3.ls("gfts-reference-data/ClimateDT/raw/" + outfile)
                    print(outfile, " already exists")
                else:
                    print("retrieve ", outfile)
                    data = retrieve(param=param, model=model, date=mid_date1 + "/to/" + end_date, levtype=levtype[param], levelist=levelist)
                    data.save(outfile)
                    cmd = "rclone copy " + outfile + " gfts:gfts-reference-data/ClimateDT/raw/"
                    os.system(cmd)
                    os.remove(outfile)
                    os.system("touch " + outfile) 
