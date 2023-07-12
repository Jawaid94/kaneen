# -*- coding: utf-8 -*-
{
    'name': "LBS arabic font",
    'author': "LBS",
    'category': 'Localization',
    'version': '15.0.0',
    'depends': ['web'],
    'license': 'OPL-1',
    'auto_install': False,
    'installable': True,

    'assets': {
        # 'web.assets_common': [
        #     'lbs_arabic_font/static/src/scss/hacenMaghreb.css'
        # ],
        'web.report_assets_common': [
            'lbs_arabic_font/static/src/scss/hacenMaghreb.css',
            'lbs_arabic_font/static/src/scss/amiri.scss',

            'lbs_arabic_font/static/src/scss/report_style.css'
        ],

    },
}
