/** @odoo-module **/

import LazyBarcodeCache from '@stock_barcode/lazy_barcode_cache';

import {patch} from 'web.utils';

patch(LazyBarcodeCache.prototype, 'kaneen_barcode', {
    /**
     * @override
     */

    setCache(cacheData) {
        for (const model in cacheData) {
            const records = cacheData[model];
            // Adds the model's key in the cache's DB.
            if (!this.dbIdCache.hasOwnProperty(model)) {
                this.dbIdCache[model] = {};
            }
            if (!this.dbBarcodeCache.hasOwnProperty(model)) {
                this.dbBarcodeCache[model] = {};
            }

            // Adds the record in the cache.
            const barcodeField = this._getBarcodeField(model);
            for (const record of records) {
                this.dbIdCache[model][record.id] = record;
                if (barcodeField) {
                    const barcode = record[barcodeField];

                    if (!this.dbBarcodeCache[model][barcode]) {
                        this.dbBarcodeCache[model][barcode] = [];
                    }
                    if (!this.dbBarcodeCache[model][barcode].includes(record.id)) {
                        this.dbBarcodeCache[model][barcode].push(record.id);
                        if (this.nomenclature && this.nomenclature.is_gs1_nomenclature && this.gs1LengthsByModel[model]) {
                            this._setBarcodeInCacheForGS1(barcode, model, record);
                        }
                    }

                    if (model == 'product.product'){
                        if (!record['barcodes']){
                            return
                        }
                        for (const barcode of record['barcodes']){
                            this.makeBarcodes(barcode, model, record)
                        }
                    }
                }
            }
        }
    },

    makeBarcodes(barcode, model, record){

        if (!this.dbBarcodeCache[model][barcode]) {
            this.dbBarcodeCache[model][barcode] = [];
        }
        if (!this.dbBarcodeCache[model][barcode].includes(record.id)) {
            this.dbBarcodeCache[model][barcode].push(record.id);
            if (this.nomenclature && this.nomenclature.is_gs1_nomenclature && this.gs1LengthsByModel[model]) {
                this._setBarcodeInCacheForGS1(barcode, model, record);
            }
        }

    }
});
