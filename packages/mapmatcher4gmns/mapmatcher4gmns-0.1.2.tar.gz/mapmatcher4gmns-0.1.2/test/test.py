import mapmatcher4gmns as m4g
import pandas as pd

def main():
    net = m4g.loadNetFromCSV(folder='data', node_file='node.csv', link_file='link.csv')

    gps_df = pd.read_csv('data/test_data_large.csv')

    matcher = m4g.mapmatching(
        network=net,
        time_field='local_time',
        time_format='%Y-%m-%dT%H:%M:%S.%fZ',
        extra_fields=['capture_time'],
        out_dir='data/result',
        result_file='matched_result.csv',
        route_file='matched_route.csv',
        core_num=4,
        batch_size=50
    )

    matcher.match(gps_df)

if __name__ == '__main__':
    main()
