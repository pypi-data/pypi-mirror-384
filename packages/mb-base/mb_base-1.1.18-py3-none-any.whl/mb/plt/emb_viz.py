## file to view pca / umap / tsne embeddings in 2d or 3d with tf projector and plotly

from mb import pandas as pd
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.preprocessing import LabelEncoder
from matplotlib import pyplot as plt
import os
import numpy as np

__all__ = ['get_emb','viz_emb','generate_sprite_images']


def get_emb(df: pd.DataFrame, emb= 'embeddings', emb_type='umap', dim=2,keep_original_emb=False,file_save=None, logger=None,**kwargs):
    """
    Visualize embeddings in 2d or 3d with tf projector and plotly

    Args:
        df (pd.DataFrame): dataframe containing embeddings. File location or DataFrame object.
        emb (str): name of embedding column
        emb_type (str, optional): embedding type. Defaults to 'umap'.
        dim (int, optional): embedding dimension. Defaults to 2.
        keep_original_emb (bool, optional): keep original embedding column. Defaults to False.
        file_save (str, optional): file location to save embeddings csv. Defaults to None.
    Output:
        df (pd.DataFrame): dataframe containing embeddings. Original embedding column is dropped.
    """
    
    if type(df) is not pd.DataFrame:
        if logger:
            logger.info('Type of df :{}'.format(str(type(df))))
        df = pd.load_any_df(df)
        if logger:
            logger.info('Loaded dataframe from path {}'.format(str(df)))
    
    if logger:
        logger.info('Data shape {}'.format(str(df.shape)))
        logger.info('Data columns {}'.format(str(df.columns)))
        logger.info('Performing {} on {} embeddings'.format(emb_type,emb))
    
    if emb_type=='pca':
        pca = PCA(n_components=dim)
        pca_emb = pca.fit_transform(list(df[emb]))
        if logger:
            logger.info('First PCA transform result : {}'.format(str(pca_emb[0])))
        temp_res = list(pca_emb)
    
    if emb_type=='tsne':
        tsne = TSNE(n_components=dim, verbose=1, perplexity=30, n_iter=250, **kwargs)
        df[emb] = df[emb].apply(lambda x: np.array(x))
        k1 = np.vstack(df[emb])
        tsne_emb = tsne.fit_transform(k1)
        if logger:
            logger.info('First TSNE transform result : {}'.format(str(tsne_emb[0])))
        temp_res = list(tsne_emb)
    
    if emb_type=='umap':
        try:
            import umap
        except ImportError:
            if logger:
                logger.info('umap not installed, installing umap')
            os.system('pip install umap-learn')
            import umap
        umap_emb = umap.UMAP(n_components=2,**kwargs).fit_transform(list(df[emb]))
        if logger:
            logger.info('First UMAP transform result : {}'.format(str(umap_emb[0])))
        temp_res = list(umap_emb)
    
    df['emb_res'] = temp_res
    if keep_original_emb==False:
        df.drop(emb,axis=1,inplace=True)
        if logger:
            logger.info('Dropped original embedding column')
            
    if file_save:
        df.to_csv(file_save + '/emb_res.csv',index=False)
    else:
        df.to_csv('./emb_res.csv',index=False)
    
    return df

def viz_emb(df: pd.DataFrame, emb_column='emb_res' , target_column='taxcode', viz_type ='plt',dash_viz=False,limit = None,image_tb=None , file_save=None,
            dont_viz=False, logger=None):
    """
    Vizualize embeddings in 2d or 3d with tf projector and plotly
    
    Args:
        df (pd.DataFrame): dataframe containing embeddings. File location or DataFrame object.
        emb_column (str): name of embedding column
        target_column (str): name of target column. It can be used to color the embeddings. Defaults to 'taxcode'. Can be None too.
        viz_type (str, optional): visualization type: 'plt','pe' or 'tf'. Defaults to 'plt'.
        dash_viz (bool, optional): if True, then it will create a dash app. Defaults to False.
        limit (int, optional): limit number of data points to visualize. Takes random samples. Defaults to None.
        image_tb (str, optional): image location column to be used in tensorboard projector if want to create with images. Defaults to None.
        file_save (str, optional): file location to save plot. If viz_type='tf', then it wont be saved. Defaults to None.
        dont_viz (bool, optional): if True, then it wont visualize. Defaults to False.
        logger (logger, optional): logger object. Defaults to None.
    Output:
        None
    """
    
    if type(df) != pd.DataFrame:
        if logger:
            logger.info('Type of df :{}'.format(str(type(df))))
        df = pd.load_any_df(df)
    
    if limit:
        df = df.sample(limit)
    
    assert emb_column in df.columns, f'Embedding column not found in dataframe: {df.columns}'
    
    emb_data = np.concatenate(np.array(df[emb_column]))
    emb_data = emb_data.reshape(-1,2) #change this for 3d
    if logger:
        logger.info('Embedding data shape {}'.format(str(emb_data.shape)))
    
    if target_column:
        target_data = list(df[target_column])
        if type(target_data[0]) == str:
            target_data = LabelEncoder().fit_transform(target_data)
        
    assert target_column==None or target_column in df.columns, f'Target column not found in dataframe : {df.columns}'
    
    if file_save == None:
        file_save = './emb_plot.png'
        
    # Visualize the embeddings using a scatter plot
    if viz_type=='plt' and target_column:
        plt.scatter(emb_data[:, 0], emb_data[:, 1], c=target_data, cmap='viridis')
        #plt.legend()
        if dont_viz==False:
            plt.show()
        if file_save:
            plt.savefig(file_save+'/emb_plot.png')

    elif viz_type=='plt' and target_column==None:       
        plt.scatter(emb_data[:, 0], emb_data[:, 1])
        #plt.legend()
        if dont_viz==False:
            plt.show()
        if file_save:
            plt.savefig(file_save+'/emb_plot.png')

    elif viz_type=='pe' and target_column:
        
        #importing plotly and dash
        import plotly.express as px
        
        if dash_viz:
            code = """

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import numpy as np

# Create the Dash app
app = dash.Dash(__name__)

# Define the layout of the app
df=pd.read_csv('./emb_res.csv')
df['emb_res_np'] = df['emb_res'].apply(lambda x:np.fromstring(x[1:-1],sep=' '))
#emb_data = np.concatenate(np.array(df['emb_res_np']))
emb_data = np.array(df['emb_res_np'].tolist())  # Convert to 2D array


app.layout = html.Div([
    dcc.Graph(
        id='scatter-plot',
        figure=px.scatter(df , x=emb_data[:, 0], y=emb_data[:, 1], color=df['menu_code'], color_continuous_scale = 'rainbow'),
        config={'staticPlot': False}),
        html.Div([html.Img(id='selected-image', style={'width': '50%'}),
        html.Div(id='hover-data-output')])])

# Define a callback function for updating the hover data
@app.callback([Output('hover-data-output', 'children'),Output('selected-image', 'src')],
        [Input('scatter-plot', 'hoverData')])

def display_hover_data(hover_data):
    if hover_data is None:
        return ("Hover over a point to see data")

    # Extract data from hover_data
    point_index = hover_data['points'][0]['pointIndex']
    target_value = df.iloc[point_index]['event_id']
    image_url = df.iloc[point_index]['after_image_url']

    return f"Hovered over point {target_value}. Image URL: {image_url}",image_url

# Run the app in the notebook
if __name__ == '__main__':
    app.run_server(mode='inline', port=8927,host='0.0.0.0')"""
            
            with open(file_save + '/dash_app.py', 'w') as f:
                f.write(code)    
        
        else:
            fig = px.scatter(x=emb_data[:, 0], y=emb_data[:, 1], color=target_data,    color_continuous_scale = 'rainbow',
                            title = f"Similarity to data visualised using dim reduction")
            fig.update_layout(width = 650,height = 650)
            if dont_viz==False:
                fig.show()
            if file_save:
                fig.write_html(file_save+'/emb_plot.html',full_html=True)

    elif viz_type=='tf' and target_column:
        
        ##check from here
        log_dir = './tp_logs'
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        emb_data = np.array(emb_data)
        loc_emb_data = os.path.join(log_dir,'emb_data_tf.tsv')
        np.savetxt(loc_emb_data, emb_data, delimiter='\t')
        
        target_data = np.array(target_data)
        loc_target_data = os.path.join(log_dir,'labels_tf.tsv')
        np.savetxt(loc_target_data,target_data,delimiter='\t')
        
        if image_tb is not None:
            loc_sprite_image = os.path.join(log_dir,'sprite_image.png')
            generate_sprite_images(df[image_tb], file_save=loc_sprite_image, img_size=28 ,logger=None)        
        
        from tensorboard.plugins import projector
        
        config = projector.ProjectorConfig()
        embedding = config.embeddings.add()
        embedding.tensor_path = loc_emb_data
        embedding.metadata_path = loc_target_data
        if image_tb is not None:
            embedding.sprite.image_path = loc_sprite_image
            embedding.sprite.single_image_dim.extend([32, 32])

        with open(os.path.join(log_dir, 'projector_config.pbtxt'), 'w') as f:
            f.write(str(config))
        
        if logger:
            logger.info('Run tensorboard --logdir={} to view embeddings'.format(log_dir))
            logger.info('if on jupyter notebook, run below code to view embeddings in notebook')
            logger.info('%load_ext tensorboard')
            logger.info('%tensorboard --logdir={}'.format(log_dir))

    
def generate_sprite_images(img_paths, file_save=None, img_size= 28 ,logger=None):
    """
    Create a sprite image consisting of images

    Args:
        img_paths (list or pd.DataFrame): list of image paths
        file_save (str, optional): file location to save sprite image. Defaults to None. Will save in current directory.
        img_size (int, optional): image size. Defaults to 28.
        logger (logger, optional): logger object. Defaults to None.
    Output:
        sprite_image (np.array): sprite image
    """
    import tensorflow as tf

    if type(img_paths) is not list:
        img_paths = list(img_paths)
    
    #create sprite image
    images = [tf.io.read_file(img_path) for img_path in img_paths]
    images = [tf.image.decode_image(img) for img in images]
    images = [tf.image.resize(img, (img_size, img_size)) for img in images]
    images = [img.numpy() for img in images]
    sprite_image = np.concatenate(images, axis=1)
    
    if file_save:
        np.save(file_save,sprite_image)
        tf.keras.utils.save_img(file_save,sprite_image)
    else:
        np.save('./sprite_image',sprite_image)
        tf.keras.utils.save_img('./sprite_image.png',sprite_image)
        
    return sprite_image
    