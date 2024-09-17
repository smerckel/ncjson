import ncjson


url = 'https://co.ifremer.fr/co/ego/ego/v2/sea017/sea017_20230613/sea017_20230613_R.nc'

#url = '../tests/data/sea017_20230613_R.nc'

with ncjson.DStoJSON(url) as writer:
    writer.write_json(write_to_stdout=False)


bb_dict = writer.get_bb()
for k, v in bb_dict.items():
    print(f"{k:25s} {v}")



