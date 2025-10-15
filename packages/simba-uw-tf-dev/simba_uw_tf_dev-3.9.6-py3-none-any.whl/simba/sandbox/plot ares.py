import random
from shapely.geometry import Polygon
from simba.utils.read_write import read_pickle, read_roi_data
from simba.utils.lookups import create_color_palettes
from simba.plotting.geometry_plotter import GeometryPlotter
from simba.utils.data import create_color_palette
#
#
# def plot_ares(graph_data, video, save_path):
#     data = read_pickle(data_path=graph_data, verbose=True)
#     num_tracks = len(data)
#     frm_cnt = max(max(id_data.keys()) for id_data in data.values())
#     results = []
#     print
#     # Fill results
#     for id, id_data in data.items():
#         a = list(id_data.values())
#         results.append(a)
#     #colors = [(230, 216, 173)] * num_tracks #(173, 216, 230) hp 255, 105, 180, 230, 216, 173
#     #intersection_clr = (180, 105, 255)
#     colors = create_color_palette(pallete_name='Set1', increments=num_tracks-1)
#     random.shuffle(colors)
#     colors = [tuple(x) for x in colors]
#     intersection_clr = None
#     plotter = GeometryPlotter(geometries=results, shape_opacity=0.5, video_name=video, core_cnt=6, colors=colors, save_dir=save_path, intersection_clr=intersection_clr)
#     #plotter = Geom etryPlotter(geometries=results, shape_opacity=0.5, video_name=video, core_cnt=6, colors=colors, save_dir=save_path, intersection_clr=intersection_clr)
#     plotter.run()

def plot_ares_2(roi_path, video, save_path):
    _, _, data = read_roi_data(roi_path)
    data = data.loc[0, 'vertices']
    p = []
    for i in range(33125):
        p.append(Polygon(data))
    colors = [(144, 238, 144)] #* 33125
    print(p)
    plotter = GeometryPlotter(geometries=[p], shape_opacity=0.60, video_name=video, core_cnt=6, colors=colors, save_dir=save_path, intersection_clr=None)
    plotter.run()

roi_path = r'/Users/simon/Desktop/envs/simba/troubleshooting/asasd/project_folder/logs/measures/ROI_definitions.h5'
graph_data = r'/Users/simon/Desktop/envs/simba/troubleshooting/ant/ant_geometries_circle.pickle'
#graph_data = r'/Users/simon/Desktop/envs/simba/troubleshooting/ant/ant_geometries.pickle'
video = r'/Users/simon/Desktop/envs/simba/troubleshooting/ant/ant_geo_points.mp4'
save_path = r'/Users/simon/Desktop/envs/simba/troubleshooting/ant/save_dir'
plot_ares_2(roi_path, video, save_path)