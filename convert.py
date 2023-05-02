import pickle
from cloudbandpy import cloudband

def convert(fin, fout):
    """
    Converts pickles files containing a list of lists of instances of
    `CloudBand` into pickle files containing a list of lists of dictionaries
    with the corresponding data

    Input:
        fin:  Input filename (str)
        fout: Output filename (str)
    """
    with open(fin, "rb") as f:
        data = pickle.load(f)
    with open(fout, "wb") as f:
        pickle.dump(
            [
                [
                    {
                        "cloud_band_array": c.cloud_band_array,
                        "date_number": c.date_number,
                        "area": c.area,
                        "lats": c.lats,
                        "lons": c.lons,
                        "connected_longitudes": c.connected_longitudes,
                        "iscloudband": c.iscloudband,
                        "parents": c.parents,
                    }
                    for c in j
                ]
                for j in data
            ],
            f,
        )


fin = "data/list_of_cloud_bands20210219.00-20210228.00-southPacific.pickle_bak"
fout = "data/list_of_cloud_bands20210219.00-20210228.00-southPacific.pickle"
convert(fin, fout)