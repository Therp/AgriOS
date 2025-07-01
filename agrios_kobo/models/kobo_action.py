# -*- coding: utf-8 -*-

from odoo import models, _
from odoo.exceptions import ValidationError

from geopy.distance import distance as geo_distance
from datetime import datetime, date
from markupsafe import Markup
import time


class KoboAssetAction(models.BaseModel):
    _inherit = 'kobo.asset.action'
    
    def farm_mapping_action(self, asset_inputs):
        raise_exp = self._context.get('raise_exp', True)
        farmer_plot_env = self.env['farmer.plot'].sudo()
        for asset_input in asset_inputs.sudo():
            try:
                values_dict = asset_input.get_inputs_dict()
                plot_name, warning_message = self._convert_received_char(values_dict, ['Plot_Name', 'plot_name'])
                farmer, warning_message = self._convert_received_int_to_record(values_dict, ['Farmer', 'farmer'], 'res.partner')
                plot_land_ownership, warning_message = self._convert_received_char(values_dict, ['Plot_Land_Ownership', 'plot_land_ownership'])
                plot_established_year, warning_message = self._convert_received_int(values_dict, ['Plot_Year_Established', 'plot_established_year'])
                plot_condition, warning_message = self._convert_received_char(values_dict, ['Plot_Condition', 'plot_condition'])
                plot_main_road, warning_message = self._convert_received_char(values_dict, ['Plot_Main_Road', 'plot_main_road'])
                plot_main_road_distance, warning_message = self._convert_received_float(values_dict, ['Plot_Main_Road_Distance', 'plot_main_road_distance'])
                plot_description, warning_message = self._convert_received_char(values_dict, ['Plot_Description', 'plot_description'])
                land_uom, warning_message = self._convert_received_char(values_dict, ['Land_UoM', 'land_uom'])
                plot_polygon, warning_message = self._convert_received_char(values_dict, ['Plot_Polygon', 'plot_polygon'])
                plot_polygon_area, warning_message = self._convert_received_float(values_dict, ['Plot_Polygon_Size_Calculation', 'plot_polygon_area'])
                if not plot_name:
                    warning_message = _(f"No Plot Name selected!")
                    if raise_exp: raise ValidationError(warning_message)
                    else: asset_input.action_warning = warning_message; continue

                #TODO add validations

                gshape_paths = {
                    'type': 'polygon',
                    'options': {
                        'paths': []
                    },
                    'lines': {},
                }

                geo_loc_points = plot_polygon.split(';')
                fisrt_point = None
                last_point = None
                path_idx = 0

                for geo_points in geo_loc_points[:-1]:
                    point = geo_points.split(' ')

                    if not fisrt_point:
                        fisrt_point = point

                    latitude, longitude, altitude, accuracy = point
                    latitude = float(latitude)
                    longitude = float(longitude)

                    gshape_paths['options']['paths'].append({
                        'lat': latitude,
                        'lng': longitude,
                    })
                    if last_point:
                        path_idx += 1
                        gshape_paths['lines'][str(path_idx)] = {
                            'start': {
                                'lat': float(last_point[0]),
                                'lng': float(last_point[1]),
                            },
                            'stop': {
                                'lat': latitude,
                                'lng': longitude,
                            },
                            'length': geo_distance((last_point[0], last_point[1]), (latitude, longitude)).m,
                        }

                    last_point = point

                path_idx += 1
                gshape_paths['lines'][str(path_idx)] = {
                    'start': {
                        'lat': float(fisrt_point[0]),
                        'lng': float(fisrt_point[1]),
                    },
                    'stop': {
                        'lat': float(last_point[0]),
                        'lng': float(last_point[1]),
                    },
                    'length': geo_distance((fisrt_point[0], fisrt_point[1]), (last_point[0], last_point[1])).m,
                }

            except Exception as exp:
                if raise_exp:
                    raise
                else:
                    asset_input.action_warning = _("Exception caught: %s") % exp


    def farmer_input_order_action(self, asset_inputs):
        raise_exp = self._context.get('raise_exp', True)
        
        sale_orders_env = self.env['sale.order'].sudo().with_context(mail_create_nolog=True)
        payment_register_env = self.env['account.payment.register'].sudo()
        
        for asset_input in asset_inputs.sudo():
            try:
                start_comp_time = time.time()
                
                values_dict = asset_input.get_inputs_dict()
                company = asset_input.asset_id.company_id
                currency = company.currency_id
                action_warning = []
                
                farmer, warning_message = self._convert_received_int_to_record(values_dict, ['farmer', 'Farmer'], 'res.partner')
                if not farmer:
                    if raise_exp: raise ValidationError(warning_message)
                    else: asset_input.action_warning = warning_message; continue
                
                pricelist = farmer.property_product_pricelist
                
                input_datetime, warning_message = self._convert_received_datetime(values_dict, ['Date_Time'])
                if not input_datetime:
                    if raise_exp: raise ValidationError(warning_message)
                    else: asset_input.action_warning = warning_message; continue
                input_date = input_datetime.date()
                
                warehouse, warning_message = self._convert_received_int_to_record(values_dict, ['warehouse', 'Warehouse'], 'stock.warehouse')
                if not warehouse:
                    if raise_exp: raise ValidationError(warning_message)
                    else: asset_input.action_warning = warning_message; continue
                
                contract = farmer.open_contract_ids
                if len(contract) > 1:
                    contract = contract.sorted(lambda l: l.season_start_date)[-1]
                
                payment_done, warning_message = self._convert_received_char(values_dict, ['Payment_Now'])
                if payment_done in ('full', 'partial'):
                    payment_amount, warning_message = self._convert_received_float(values_dict, ['amount_paid', 'Amount_Paid_Calculation'])
                    if payment_amount is None:
                        if raise_exp: raise ValidationError(warning_message)
                        else: asset_input.action_warning = warning_message; continue
                    
                    payment_journal, warning_message = self._convert_received_int_to_record(values_dict, ['payment_method', 'Payment_Method'], 'account.journal')
                    if not payment_journal:
                        if raise_exp: raise ValidationError(warning_message)
                        else: asset_input.action_warning = warning_message; continue
                    
                    payment_receipt_number, warning_message = self._convert_received_char(values_dict, ['Payment_Receipt_Number'])
                
                order_line = []
                
                input_products_section_key = 'Input_Products_Repeat'
                input_products_list, warning_message = self._convert_received_group_to_list(values_dict, [input_products_section_key])
                if not input_products_list:
                    if not warning_message:
                        warning_message = _('No input products received from the survey input')
                    if raise_exp: raise ValidationError(warning_message)
                    else: asset_input.action_warning = warning_message; continue
                
                continue_loop = False
                
                for input_product_data in input_products_list:
                    product, warning_message = self._convert_received_int_to_record(input_product_data, [f'{input_products_section_key}/Input_Products_Group/Input_Product'], 'product.product')
                    if not product:
                        if raise_exp: raise ValidationError(warning_message)
                        else:
                            asset_input.action_warning = warning_message
                            continue_loop = True; break
                    
                    qty, warning_message = self._convert_received_float(input_product_data, [f'{input_products_section_key}/Input_Products_Group3/Input_Product_Quantity'])
                    if not qty:
                        if not warning_message: warning_message = _('No quantity was reported on a input order line')
                        if raise_exp: raise ValidationError(warning_message)
                        else:
                            asset_input.action_warning = warning_message
                            continue_loop = True; break
                    
                    input_price_unit, warning_message = self._convert_received_float(input_product_data, [f'{input_products_section_key}/Input_Products_Group2/Input_Product_Price_Calculation'])
                    price_unit = currency.round(pricelist._get_product_price(product, quantity=qty, currency=currency, uom=product.uom_id, date=input_date))
                    
                    if input_price_unit is not None and price_unit != input_price_unit:
                        action_warning.append(_(f"The price unit for the product {product.name} received ({input_price_unit}) is different from the farmer pricelist ({pricelist.name}) price ({price_unit})!"))
                    
                    order_line.append((0,0,{
                        'product_id': product.id,
                        'product_template_id': product.product_tmpl_id.id,
                        'name': product.description_sale or product.name,
                        'product_uom_qty': qty,
                        'product_uom': product.uom_id.id,
                        'price_unit': price_unit,
                        'tax_id': [(6,0,product.taxes_id.ids)],
                    }))
                
                if continue_loop:
                    continue
                
                sale_order = sale_orders_env.create({
                    'partner_id': farmer.id,
                    'partner_invoice_id': farmer.id,
                    'partner_shipping_id': farmer.id,
                    'date_order': input_datetime,
                    'warehouse_id': warehouse.id,
                    'company_id': company.id,
                    'pricelist_id': pricelist.id,
                    'origin': f'Kobo Input {asset_input.id}',
                    'oms_oa_id': contract.id,
                    'order_line': order_line,
                })
                
                sale_order.message_post(body=Markup(_('Created via Kobo input %s') % asset_input._get_html_link()))
                
                try:
                    sale_order.action_confirm()
                except Exception as exp:
                    warning_message = _(f'An error was raised when trying to confirm the sale order: {exp}')
                    if raise_exp: raise ValidationError(warning_message)
                    else: asset_input.action_warning = warning_message; continue
                
                if sale_order.invoice_status == 'to invoice':
                    try:
                        invoices = sale_order._create_invoices(date=input_date)
                    except Exception as exp:
                        warning_message = _(f'An error was raised when trying to create the sale order invoice: {exp}')
                        if raise_exp: raise ValidationError(warning_message)
                        else: asset_input.action_warning = warning_message; continue
                
                try:
                    for delivery in sale_order.picking_ids:
                        for stk_mv in delivery.move_ids_without_package:
                            stk_mv.quantity = stk_mv.product_uom_qty
                        delivery.button_validate()
                except Exception as exp:
                    warning_message = _(f'An error was raised when trying to validate the delivery order: {exp}')
                    if raise_exp: raise ValidationError(warning_message)
                    else: asset_input.action_warning = warning_message; continue
                
                if sale_order.invoice_status == 'to invoice':
                    try:
                        invoices = sale_order._create_invoices(date=input_date)
                    except Exception as exp:
                        warning_message = _(f'An error was raised when trying to create the sale order invoice: {exp}')
                        if raise_exp: raise ValidationError(warning_message)
                        else: asset_input.action_warning = warning_message; continue
                
                try:
                    for invoice in sale_order.invoice_ids.with_context(validate_analytic=False):
                        invoice.invoice_date = input_date
                        invoice.action_post()
                except Exception as exp:
                    warning_message = _(f'An error was raised when trying to post the sale order invoice: {exp}')
                    if raise_exp: raise ValidationError(warning_message)
                    else: asset_input.action_warning = warning_message; continue
                
                if payment_done in ('full', 'partial'):
                    if payment_receipt_number:
                        payment_memo = f'{sale_order.name} - {payment_receipt_number}'
                    else:
                        payment_memo = sale_order.name
                    
                    if payment_amount >= sale_order.amount_total:
                        payment_difference_handling = 'reconcile'
                    else:
                        payment_difference_handling = 'open'
                    
                    try:
                        payment_register = payment_register_env.with_context(active_model='account.move.line', active_ids=sale_order.invoice_ids.line_ids.ids).create({
                            'amount': payment_amount,
                            'communication': payment_memo,
                            'currency_id': currency.id,
                            'journal_id': payment_journal.id,
                            'payment_type': 'inbound',
                            'partner_type': 'customer',
                            'partner_id': farmer.id,
                            'payment_difference_handling': payment_difference_handling,
                        })
                        payment_register._create_payments()
                        
                    except Exception as exp:
                        warning_message = _(f'An error was raised when trying to record the bill payment: {exp}')
                        if raise_exp: raise ValidationError(warning_message)
                        else: asset_input.action_warning = warning_message; continue
                
                asset_input.write({
                    'action_id': self.id,
                    'partner_ids': [(6,0,farmer.ids)],
                    'action_warning': '\n\n'.join(action_warning),
                    'action_ref': f'sale.order,{sale_order.id}',
                    'action_comp_time': (time.time() - start_comp_time),
                })
                
            except Exception as exp:
                if raise_exp:
                    raise
                else:
                    asset_input.action_warning = _("Exception caught: %s") % exp
    
    def farmer_offtake_action(self, asset_inputs):
        raise_exp = self._context.get('raise_exp', True)
        
        purchase_orders_env = self.env['purchase.order'].sudo().with_context(mail_create_nolog=True)
        payment_register_env = self.env['account.payment.register'].sudo()
        
        for asset_input in asset_inputs.sudo():
            try:
                start_comp_time = time.time()
                
                values_dict = asset_input.get_inputs_dict()
                company = asset_input.asset_id.company_id
                action_warning = []
                
                farmer, warning_message = self._convert_received_int_to_record(values_dict, ['farmer', 'Farmer'], 'res.partner')
                if not farmer:
                    if raise_exp: raise ValidationError(warning_message)
                    else: asset_input.action_warning = warning_message; continue
                
                offtake_datetime, warning_message = self._convert_received_datetime(values_dict, ['Date_Time'])
                if not offtake_datetime:
                    if raise_exp: raise ValidationError(warning_message)
                    else: asset_input.action_warning = warning_message; continue
                
                warehouse, warning_message = self._convert_received_int_to_record(values_dict, ['warehouse', 'Warehouse'], 'stock.warehouse')
                if not warehouse:
                    if raise_exp: raise ValidationError(warning_message)
                    else: asset_input.action_warning = warning_message; continue
                
                if not warehouse.in_type_id:
                    warning_message = _(f"The warehouse {warehouse.display_name} does not have the delivery 'In Type' defined!")
                    if raise_exp: raise ValidationError(warning_message)
                    else: asset_input.action_warning = warning_message; continue
                
                product, warning_message = self._convert_received_int_to_record(values_dict, ['offtake_product', 'Offtake_Product'], 'product.product')
                if not product:
                    if raise_exp: raise ValidationError(warning_message)
                    else: asset_input.action_warning = warning_message; continue
                
                qty, warning_message = self._convert_received_float(values_dict, ['Offtake_Product_Quantity'])
                if not qty:
                    if raise_exp: raise ValidationError(warning_message)
                    else: asset_input.action_warning = warning_message; continue
                
                price_unit, warning_message = self._convert_received_float(values_dict, ['Offtake_Product_Price'])
                if price_unit is None:
                    if raise_exp: raise ValidationError(warning_message)
                    else: asset_input.action_warning = warning_message; continue
                
                contract = farmer.open_contract_ids.filtered(lambda cont: cont.contracted_crop_id == product)
                if len(contract) > 1:
                    contract = contract.sorted(lambda l: l.season_start_date)[-1]
                
                payment_done, warning_message = self._convert_received_char(values_dict, ['Payment_Now'])
                if payment_done in ('full', 'partial'):
                    payment_amount, warning_message = self._convert_received_float(values_dict, ['amount_paid', 'Amount_Paid_Calculation'])
                    if payment_amount is None:
                        if raise_exp: raise ValidationError(warning_message)
                        else: asset_input.action_warning = warning_message; continue
                    
                    payment_journal, warning_message = self._convert_received_int_to_record(values_dict, ['payment_method', 'Payment_Method'], 'account.journal')
                    if not payment_journal:
                        if raise_exp: raise ValidationError(warning_message)
                        else: asset_input.action_warning = warning_message; continue
                    
                    payment_receipt_number, warning_message = self._convert_received_char(values_dict, ['Payment_Receipt_Number'])
                
                purchase_order = purchase_orders_env.create({
                    'partner_id': farmer.id,
                    'date_order': offtake_datetime,
                    'picking_type_id': warehouse.in_type_id.id,
                    'currency_id': company.currency_id.id,
                    'company_id': company.id,
                    'oms_oa_id': contract.id,
                    'order_line': [(0,0,{
                        'product_id': product.id,
                        'name': product.description_purchase or product.name,
                        'product_qty': qty,
                        'product_uom': product.uom_id.id,
                        'price_unit': price_unit,
                        'taxes_id': [(6,0,product.supplier_taxes_id.ids)],
                    })],
                })
                
                purchase_order.message_post(body=Markup(_('Created via Kobo input %s') % asset_input._get_html_link()))
                
                try:
                    purchase_order.button_confirm()
                except Exception as exp:
                    warning_message = _(f'An error was raised when trying to confirm the purchase order: {exp}')
                    if raise_exp: raise ValidationError(warning_message)
                    else: asset_input.action_warning = warning_message; continue
                
                try:
                    for delivery in purchase_order.picking_ids:
                        delivery.button_validate()
                except Exception as exp:
                    warning_message = _(f'An error was raised when trying to validate the delivery order: {exp}')
                    if raise_exp: raise ValidationError(warning_message)
                    else: asset_input.action_warning = warning_message; continue
                
                try:
                    purchase_order.action_create_invoice()
                except Exception as exp:
                    warning_message = _(f'An error was raised when trying to create the purchase order bill: {exp}')
                    if raise_exp: raise ValidationError(warning_message)
                    else: asset_input.action_warning = warning_message; continue
                
                try:
                    for invoice in purchase_order.invoice_ids.with_context(validate_analytic=False):
                        invoice.invoice_date = offtake_datetime.date()
                        invoice.action_post()
                except Exception as exp:
                    warning_message = _(f'An error was raised when trying to post the purchase order bill: {exp}')
                    if raise_exp: raise ValidationError(warning_message)
                    else: asset_input.action_warning = warning_message; continue
                
                if payment_done in ('full', 'partial'):
                    if payment_receipt_number:
                        payment_memo = f'{purchase_order.name} - {payment_receipt_number}'
                    else:
                        payment_memo = purchase_order.name
                    
                    if payment_amount >= purchase_order.amount_total:
                        payment_difference_handling = 'reconcile'
                    else:
                        payment_difference_handling = 'open'
                    
                    try:
                        payment_register = payment_register_env.with_context(active_model='account.move.line', active_ids=purchase_order.invoice_ids.line_ids.ids).create({
                            'amount': payment_amount,
                            'communication': payment_memo,
                            'currency_id': company.currency_id.id,
                            'journal_id': payment_journal.id,
                            'payment_type': 'outbound',
                            'partner_type': 'supplier',
                            'partner_id': farmer.id,
                            'payment_difference_handling': payment_difference_handling,
                            
                        })
                        payment_register._create_payments()
                        
                    except Exception as exp:
                        warning_message = _(f'An error was raised when trying to record the bill payment: {exp}')
                        if raise_exp: raise ValidationError(warning_message)
                        else: asset_input.action_warning = warning_message; continue
                
                asset_input.write({
                    'action_id': self.id,
                    'partner_ids': [(6,0,farmer.ids)],
                    'action_warning': '\n\n'.join(action_warning),
                    'action_ref': f'purchase.order,{purchase_order.id}',
                    'action_comp_time': (time.time() - start_comp_time),
                })
                
            except Exception as exp:
                if raise_exp:
                    raise
                else:
                    asset_input.action_warning = _("Exception caught: %s") % exp
    
    def farmer_interaction_action(self, asset_inputs):
        raise_exp = self._context.get('raise_exp', True)
        
        farmer_interaction_env = self.env['farmer.interaction'].sudo().with_context(mail_create_nolog=True)
        
        for asset_input in asset_inputs.sudo():
            try:
                start_comp_time = time.time()
                
                values_dict = asset_input.get_inputs_dict()
                company = asset_input.asset_id.company_id
                action_warning = []
                
                name, warning_message = self._convert_received_char(values_dict, ['Summary'])
                if not name:
                    if raise_exp: raise ValidationError(warning_message)
                    else: asset_input.action_warning = warning_message; continue
                
                interaction_type, warning_message = self._convert_received_char(values_dict, ['interaction', 'Interaction'])
                if not interaction_type:
                    if raise_exp: raise ValidationError(warning_message)
                    else: asset_input.action_warning = warning_message; continue
                
                farmer, warning_message = self._convert_received_int_to_record(values_dict, ['farmer', 'Farmer'], 'res.partner')
                if not farmer:
                    if raise_exp: raise ValidationError(warning_message)
                    else: asset_input.action_warning = warning_message; continue
                
                interaction_date, warning_message = self._convert_received_date(values_dict, ['Interaction_Date'])
                if not interaction_date:
                    if raise_exp: raise ValidationError(warning_message)
                    else: asset_input.action_warning = warning_message; continue
                
                notes, warning_message = self._convert_received_char(values_dict, ['Notes'])
                if not notes:
                    if raise_exp: raise ValidationError(warning_message)
                    else: asset_input.action_warning = warning_message; continue
                
                new_interaction_values = {
                    'name': name,
                    'outgrower_id': farmer.id,
                    'interaction_date': interaction_date,
                    'interaction_type': interaction_type,
                    'notes': notes,
                }
                
                try:
                    interaction_extra_vals = self._farmer_interaction_action_get_interaction_extra_vals(values_dict, action_warning)
                    new_interaction_values.update(interaction_extra_vals)
                except Exception as exp:
                    if raise_exp: raise
                    else: asset_input.action_warning = str(exp);
                
                interaction = farmer_interaction_env.create(new_interaction_values)
                
                interaction.message_post(body=Markup(_('Created via Kobo input %s') % asset_input._get_html_link()))
                
                asset_input.write({
                    'action_id': self.id,
                    'partner_ids': [(6,0,farmer.ids)],
                    'action_warning': '\n\n'.join(action_warning),
                    'action_ref': f'farmer.interaction,{interaction.id}',
                    'action_comp_time': (time.time() - start_comp_time),
                })
                
            except Exception as exp:
                if raise_exp:
                    raise
                else:
                    asset_input.action_warning = _("Exception caught: %s") % exp
    
    def _farmer_interaction_action_get_interaction_extra_vals(self, values_dict, action_warning_list):
        return {}  # to be inherited
    
    def farmer_training_attendance_action(self, asset_inputs):
        raise_exp = self._context.get('raise_exp', True)
        
        farmer_trainings_env = self.env['farmer.training'].sudo().with_context(mail_create_nolog=True)
        training_types_env = self.env['og.training'].sudo().with_context(active_test=False)
        
        for asset_input in asset_inputs.sudo():
            try:
                start_comp_time = time.time()
                
                values_dict = asset_input.get_inputs_dict()
                company = asset_input.asset_id.company_id
                
                training_date, warning_message = self._convert_received_date(values_dict, ['Training_Date'])
                if not training_date:
                    if raise_exp: raise ValidationError(warning_message)
                    else: asset_input.action_warning = warning_message; continue
                
                location, warning_message = self._convert_received_char(values_dict, ['location', 'Location'])
                if not location:
                    if raise_exp: raise ValidationError(warning_message)
                    else: asset_input.action_warning = warning_message; continue
                
                start_time, warning_message = self._convert_received_time(values_dict, ['start_training', 'Start_Time_Training'])
                if not start_time:
                    if raise_exp: raise ValidationError(warning_message)
                    else: asset_input.action_warning = warning_message; continue
                
                duration, warning_message = self._convert_received_float(values_dict, ['duration_training', 'Duration'])
                if not duration:
                    if raise_exp: raise ValidationError(warning_message)
                    else: asset_input.action_warning = warning_message; continue
                
                trainer, warning_message = self._convert_received_int_to_record(values_dict, ['trainer', 'Trainer'], 'res.partner')
                if not trainer:
                    if raise_exp: raise ValidationError(warning_message)
                    else: asset_input.action_warning = warning_message; continue
                
                training_ids = []
                trainings_txt, warning_message = self._convert_received_char(values_dict, ['Training_Topics'])
                if not trainings_txt:
                    if raise_exp: raise ValidationError(warning_message)
                    else: asset_input.action_warning = warning_message; continue
                for training_txt in trainings_txt.split(' '):
                    if not training_txt:
                        continue
                    training_type = training_types_env.browse(int(training_txt))
                    if not training_type:
                        warning_message = _(f"The training subject '{training_txt}' wasn't found on the system!")
                        if raise_exp: raise ValidationError(warning_message)
                        else: asset_input.action_warning = warning_message; continue
                    training_ids.append(training_type.id)
                if not training_ids:
                    warning_message = _(f"No training subjects selected!")
                    if raise_exp: raise ValidationError(warning_message)
                    else: asset_input.action_warning = warning_message; continue
                
                coop, warning_message = self._convert_received_int_to_record(values_dict, ['community', 'Community'], 'cooperative')
                if not coop:
                    if raise_exp: raise ValidationError(warning_message)
                    else: asset_input.action_warning = warning_message; continue
                
                farmer_groups_section_key = 'Farmer_Group_Details_Repeat'
                farmers_section_key = 'Farmer_Details_Repeat'
                farmer_groups_list, warning_message = self._convert_received_group_to_list(values_dict, [farmer_groups_section_key])
                if not farmer_groups_list:
                    if not warning_message:
                        warning_message = _('No farmer group found on the survey input')
                    if raise_exp: raise ValidationError(warning_message)
                    else: asset_input.action_warning = warning_message; continue
                
                continue_loop = False
                
                coop = None
                farmer_ids = []
                group_ids = []
                farmers_data = {}
                for farmer_group_data in farmer_groups_list:
                    farmer_group, warning_message = self._convert_received_int_to_record(farmer_group_data, [f'{farmer_groups_section_key}/Farmer_Group'], 'farmer.group')
                    if not farmer_group:
                        if raise_exp: raise ValidationError(warning_message)
                        else:
                            asset_input.action_warning = warning_message
                            continue_loop = True; break
                    
                    farmers_list = farmer_group_data.get(f'{farmer_groups_section_key}/{farmers_section_key}')
                    if not farmers_list:
                        warning_message = _(f'No Farmer_Details_Repeat group found on the Farmer_Group {farmer_group.display_name}')
                        if raise_exp: raise ValidationError(warning_message)
                        else:
                            asset_input.action_warning = warning_message
                            continue_loop = True; break
                    
                    for farmer_data in farmers_list:
                        farmer, warning_message = self._convert_received_int_to_record(farmer_data, [f'{farmer_groups_section_key}/{farmers_section_key}/Farmer'], 'res.partner')
                        if not farmer:
                            if raise_exp: raise ValidationError(warning_message)
                            else:
                                asset_input.action_warning = warning_message
                                continue_loop = True; break
                        
                        farmer_ids.append(farmer.id)
                    
                    if continue_loop:
                        break
                    
                    group_ids.append(farmer_group.id)
                    coop = farmer_group.coop_id
                
                if continue_loop:
                    continue
                
                farmer_training = farmer_trainings_env.create({
                    'training_participants_ids': [(6,0,farmer_ids)],
                    'training_ids': [(6,0,training_ids)],
                    'farmer_group_ids': [(6,0,group_ids)],
                    'trainer_id': trainer.id,
                    'training_state': 'done',
                    'training_date': training_date,
                    'training_start_time': start_time,
                    'training_duration': duration,
                    'training_location': location,
                    'training_type': 'internal',
                    'coop_id': coop.id,
                })
                
                farmer_training.message_post(body=Markup(_('Created via Kobo input %s') % asset_input._get_html_link()))
                
                input_partner_ids = (farmer_ids + [trainer.id])
                
                asset_input.write({
                    'partner_ids': [(6, 0, input_partner_ids)],
                    'action_id': self.id,
                    'action_warning': False,
                    'action_ref': f'farmer.training,{farmer_training.id}',
                    'action_comp_time': (time.time() - start_comp_time),
                })
            
            except Exception as exp:
                if raise_exp:
                    raise
                else:
                    asset_input.action_warning = _("Exception caught: %s") % exp
    
    def farmer_registration_action(self, asset_inputs):
        raise_exp = self._context.get('raise_exp', True)
        
        farmer_groups_env = self.env['farmer.group'].sudo().with_context(mail_create_nolog=True)
        farmers_env = self.env['res.partner'].sudo().with_context(mail_create_nolog=True)
        farmer_contracts_env = self.env['offtake.agreement'].sudo().with_context(mail_create_nolog=True)
        users_env = self.env['res.users'].sudo()
        encaps_farmers_env = self.env['kobo.input.farmers'].sudo()
        
        for asset_input in asset_inputs.sudo():
            try:
                start_comp_time = time.time()
                
                asset_input_link = asset_input._get_html_link()
                values_dict = asset_input.get_inputs_dict()
                company = asset_input.asset_id.company_id
                action_warning = []
                
                farmers_created = self.env['res.partner']
                
                season, season_warning_message = self._convert_received_int_to_record(values_dict, ['Season'], 'season')
                
                group_type, warning_message = self._convert_received_char(values_dict, ['Farmer_Group_Type'])
                if not group_type:
                    if raise_exp: raise ValidationError(warning_message)
                    else: asset_input.action_warning = warning_message; continue
                
                if group_type == 'existing':
                    farmer_group, warning_message = self._convert_received_int_to_record(values_dict, ['existing_farmer_group_id', 'Existing_Farmer_Group'], 'farmer.group')
                    if not farmer_group:
                        if raise_exp: raise ValidationError(warning_message)
                        else: asset_input.action_warning = warning_message; continue
                    
                    coop = farmer_group.coop_id
                
                elif group_type == 'new':
                    group_name, warning_message = self._convert_received_char(values_dict, ['New_Farmer_Group_Name'])
                    if not group_name:
                        if raise_exp: raise ValidationError(warning_message)
                        else: asset_input.action_warning = warning_message; continue
                    
                    coop, warning_message = self._convert_received_int_to_record(values_dict, ['new_community', 'New_Community'], 'cooperative')
                    if not coop:
                        if raise_exp: raise ValidationError(warning_message)
                        else: asset_input.action_warning = warning_message; continue
                    
                    farmer_group = farmer_groups_env.search([('name','=',group_name),('coop_id','=',coop.id)])
                    if not farmer_group:
                        farmer_group = farmer_groups_env.create({
                            'name': group_name,
                            'coop_id': coop.id,
                        })
                        farmer_group.message_post(body=Markup(_('Created via Kobo input %s') % asset_input_link))
                    
                else:
                    warning_message = _("Unexpected value received from 'Farmer_Group_Type', expecting only 'existing' or 'new' but received '%s'") % group_type
                    if raise_exp: raise ValidationError(warning_message)
                    else: asset_input.action_warning = warning_message; continue
                
                if not coop.community_facilitator_id:
                    community_facilitator_name, warning_message = self._convert_received_char(values_dict, ['New_Technical_Coordinator_Calculation'])
                    if community_facilitator_name:
                        community_facilitator = users_env.search([('name','=ilike',community_facilitator_name)])
                        if len(community_facilitator) == 1:
                            coop.community_facilitator_id = community_facilitator
                
                geopoint, warning_message = self._convert_received_char(values_dict, ['start-geopoint'])
                if geopoint:
                    partner_latitude, partner_longitude = geopoint.split(' ')[:2]
                else:
                    partner_latitude, partner_longitude = None
                    action_warning.append(warning_message)
                
                farmers_section_key = 'Farmers_Registration_Repeat'
                farmers_data_list, warning_message = self._convert_received_group_to_list(values_dict, [farmers_section_key])
                if not farmers_data_list:
                    if raise_exp: raise ValidationError(warning_message)
                    else: asset_input.action_warning = warning_message; continue
                
                continue_loop = False
                
                farmers_contracts_section_key = f'{farmers_section_key}/Farmers_Registration_Repeat_Group5/Contracts_Repeat'
                
                for farmer_data_list in farmers_data_list:
                    farmer_name, warning_message = self._convert_received_char(farmer_data_list, [f'{farmers_section_key}/Farmers_Registration_Repeat_Group/Farmer_Name'])
                    if not farmer_name:
                        if raise_exp: raise ValidationError(warning_message)
                        else:
                            asset_input.action_warning = warning_message
                            continue_loop = True; break
                    farmer_name = farmer_name.strip()
                    
                    date_of_birth, warning_message = self._convert_received_char(farmer_data_list, [f'{farmers_section_key}/Farmers_Registration_Repeat_Group/Date_Of_Birth'])
                    if not date_of_birth:
                        action_warning.append(warning_message)
                    
                    gender, warning_message = self._convert_received_char(farmer_data_list, [f'{farmers_section_key}/Farmers_Registration_Repeat_Group/Farmer_Gender'])
                    if not gender:
                        action_warning.append(warning_message)
                    
                    phone_number, warning_message = self._convert_received_char(farmer_data_list, [f'{farmers_section_key}/Farmers_Registration_Repeat_Group/Phone'])
                    if not phone_number:
                        action_warning.append(warning_message)
                    
                    id_number, warning_message = self._convert_received_char(farmer_data_list, [f'{farmers_section_key}/Farmers_Registration_Repeat_Group2/ID_Number'])
                    if not id_number:
                        action_warning.append(warning_message)
                                        
                    mobile, warning_message = self._convert_received_char(farmer_data_list, [f'{farmers_section_key}/Farmers_Registration_Repeat_Group2/Momo_Number'])
                    if not mobile:
                        action_warning.append(warning_message)
                    
                    role, warning_message = self._convert_received_char(farmer_data_list, [f'{farmers_section_key}/Farmers_Registration_Repeat_Group3/Role', f'{farmers_section_key}/Farmers_Registration_Repeat_Group2/Role'])
                    if not role:
                        action_warning.append(warning_message)
                    
                    farm_acreage, warning_message = self._convert_received_float(farmer_data_list, [f'{farmers_section_key}/Farmers_Registration_Repeat_Group4/Own_Farm'])
                    if farm_acreage is None:
                        action_warning.append(warning_message)
                    
                    leased_acreage, warning_message = self._convert_received_float(farmer_data_list, [f'{farmers_section_key}/Farmers_Registration_Repeat_Group4/Leased_Farm'])
                    if leased_acreage is None:
                        action_warning.append(warning_message)
                    
                    attachments_dict = asset_input.get_attachments_dict()
                    image_1920 = None
                    picture_file_name, warning_message = self._convert_received_char(farmer_data_list, [f'{farmers_section_key}/Picture/Picture_001',f'{farmers_section_key}/Picture/Picture'])
                    if picture_file_name:
                        clean_picture_file_name = picture_file_name.replace(' ', '_')
                        picture_input_attachment = attachments_dict.get(clean_picture_file_name)
                        if picture_input_attachment:
                            image_1920 = picture_input_attachment.download_file(return_attachment=False)
                    
                    harvest_crop_ids = []
                    offtake_agreements_vals = []
                    farmer_contracts_data_list, warning_message = self._convert_received_group_to_list(farmer_data_list, [farmers_contracts_section_key])
                    if farmer_contracts_data_list:
                        if not season:
                            if raise_exp: raise ValidationError(season_warning_message)
                            else:
                                asset_input.action_warning = season_warning_message
                                continue_loop = True; break
                        
                        outgrower_requires_contract = True
                        
                        for farmer_contract_data_list in farmer_contracts_data_list:
                            contract_product, warning_message = self._convert_received_int_to_record(farmer_contract_data_list, [f'{farmers_contracts_section_key}/Harvest_Product'], 'product.product')
                            if not contract_product:
                                if raise_exp: raise ValidationError(warning_message)
                                else: asset_input.action_warning = warning_message; continue
                            
                            contracted_farm_acreage, warning_message = self._convert_received_float(farmer_contract_data_list, [f'{farmers_contracts_section_key}/Contracted_Farm'])
                            if not contracted_farm_acreage:
                                if raise_exp: raise ValidationError(warning_message)
                                else: asset_input.action_warning = warning_message; continue
                            
                            offtake_agreements_vals.append({
                                'season_id': season.id,
                                'contracted_crop_id': contract_product.id,
                                'contracted_farm_acreage': contracted_farm_acreage,
                                'offtake_qty': contract_product.est_yield * contracted_farm_acreage,
                            })
                            
                            harvest_crop_ids.append((4,contract_product.id))
                    
                    else:
                        outgrower_requires_contract = False
                    
                    try:
                        extra_farmer_data = self._farmer_registration_action_get_farmer_extra_vals(farmer_data_list, action_warning)
                    except Exception as exp:
                        if raise_exp: raise
                        else:
                            asset_input.action_warning = str(exp);
                            continue_loop = True; continue
                    
                    farmer = farmers_env.create({
                        'is_outgrower': True,
                        'name': farmer_name,
                        'birthday': date_of_birth,
                        'gender': gender,
                        'phone': phone_number,
                        'outgrower_identification': id_number,
                        'mobile': mobile,
                        'farmer_group_id': farmer_group.id,
                        'coop_id': coop.id,
                        'outgrower_requires_contract': outgrower_requires_contract,
                        'company_id': company.id,
                        'image_1920': image_1920,
                        'harvest_crop_ids': harvest_crop_ids,
                        'partner_latitude': partner_latitude,
                        'partner_longitude': partner_longitude,
                        **extra_farmer_data,
                    })
                    
                    if not farmer.plot_ids and (farm_acreage or leased_acreage):
                        farmer.farm_acreage = farm_acreage or 0.0
                        farmer.leased_acreage = leased_acreage or 0.0
                        farmer.total_land_size = (farm_acreage or 0.0) + (leased_acreage or 0.0)
                    
                    farmer.message_post(body=Markup(_('Created via Kobo input %s') % asset_input_link))
                    
                    farmer.verify_outgrower()
                    
                    for offtake_agreement_vals in offtake_agreements_vals:
                        offtake_agreement_vals['outgrower_id'] = farmer.id
                        contract = farmer_contracts_env.create(offtake_agreement_vals)
                        contract.message_post(body=Markup(_('Created via Kobo input %s') % asset_input_link))
                    
                    if role == 'chairperson':
                        farmer_group.chairperson_id = farmer
                    elif role == 'secretary':
                        farmer_group.group_sec_id = farmer
                    elif role == 'treasurer':
                        farmer_group.group_treasurer_id = farmer
                    
                    try:
                        self._farmer_registration_action_post_farmer_creation(farmer)
                    except Exception as exp:
                        if raise_exp: raise
                        else: 
                            asset_input.action_warning = str(exp); 
                            continue_loop = True; continue
                    
                    farmers_created += farmer
                
                if continue_loop:
                    continue
                
                if len(farmers_created) > 1:
                    ref_obj = encaps_farmers_env.create({
                        'partner_ids': [(6,0,farmers_created.ids)],
                        'input_id': asset_input.id,
                    })
                else:
                    ref_obj = farmers_created
                
                asset_input.write({
                    'action_id': self.id,
                    'partner_ids': [(6,0,farmers_created.ids)],
                    'action_warning': '\n\n'.join(action_warning),
                    'action_ref': f'{ref_obj._name},{ref_obj.id}',
                    'action_comp_time': (time.time() - start_comp_time),
                })
                
            except Exception as exp:
                if raise_exp:
                    raise
                else:
                    asset_input.action_warning = _("Exception caught: %s") % exp
    
    def _farmer_registration_action_get_farmer_extra_vals(self, farmer_data_list, action_warning_list):
        return {}  # to be inherited
    
    def _farmer_registration_action_post_farmer_creation(self, farmer):
        pass  # to be inherited
    