''' run all avaiable metrics/ transforms '''
# Author: Matt Clifford <matt.clifford@bristol.ac.uk>
# License: BSD 3-Clause License

import IQM_Vis

def run():
    # data = IQM_Vis.dataset_holder(IQM_Vis.examples.images.DEFAULT_IMAGES,
    #                               IQM_Vis.metrics.get_all_metrics(),
    #                               IQM_Vis.metrics.get_all_metric_images()
    #                               )


    # IQM_Vis.make_UI(data,
    #                 IQM_Vis.transforms.get_all_transforms(),
    #                 restrict_options=3
    #                 )
    IQM_Vis.make_UI()

if __name__ == '__main__':
    run()
