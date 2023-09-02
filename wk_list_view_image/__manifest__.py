{
    'name': "Product Images In Order Lines",

    'summary': """
        View product images in list view/order line.""",

    'description': """
        """,

    'author': "Jawaid Iqbal",
    'website': "https://www.linkedin.com/in/muhammad-jawaid-iqbal-659a6898/",

    'category': 'Uncategorized',
    'version': '15.0.2.0.2',

    'depends': ['sale', 'purchase', 'stock'],

    'data': [
        'views/views.xml',
    ],

    'assets': {
        'web.assets_backend': [
            'wk_list_view_image/static/src/css/wk_image.css',
        ],
    },
}