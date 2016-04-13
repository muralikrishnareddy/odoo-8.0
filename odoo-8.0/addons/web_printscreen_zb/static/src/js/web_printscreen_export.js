openerp.web_printscreen_zb = function(instance, m) {
    
    var _t = instance.web._t;
    var QWeb = instance.web.qweb;
    
    instance.web.ListView.include({
        load_list: function () {
            var self = this;
            this._super.apply(this, arguments);
            //self.$pager.find(".oe_list_button_import_excel").unbind('click').click(function(event){self.export_to_excel("excel")})
            //self.$pager.find(".oe_list_button_import_pdf").unbind('click').click(function(event){self.export_to_excel("pdf")})
            self.$el.find('.oe_bold oe_list_button_import_excel').on('click', self.on_sidebar_export_view_xls);
            var links = document.getElementsByClassName("oe_list_button_import_excel");
            if (links && links[0]){
                links[0].onclick = function() {
                    self.on_sidebar_export_view_xls();
                };
            }         
        },
        
	fetchval: function(id_val){
	 //retval = new instance.web.Model("inward.register").call('write', [[parseInt(id_val)], {'exported':true}]);
	 //return new instance.web.Model("crm.helpdesk").call('read',[id_val, []]);
	 return new instance.web.Model("crm.helpdesk").call('get_report_details',[id_val, []]);	 
	},
        export_to_excel: function(export_type) {
            var self = this
            var export_type = export_type
            view = this.getParent()
            // Find Header Element
            header_eles = self.$el.find('.oe_list_header_columns')
            header_name_list = []
            $.each(header_eles,function(){
                $header_ele = $(this)
                header_td_elements = $header_ele.find('th')
                $.each(header_td_elements,function(){
                    $header_td = $(this)
                    text = $header_td.text().trim() || ""
                    data_id = $header_td.attr('data-id')
                    if (text && !data_id){
                        data_id = 'group_name'
                    }
                    header_name_list.push({'header_name': text.trim(), 'header_data_id': data_id});
                   // }
                });
            });
            
            //Find Data Element
            data_eles = self.$el.find('.oe_list_content > tbody > tr')
            export_data = []
            $.each(data_eles,function(){
                data = []
                $data_ele = $(this)
                is_analysis = false
                if ($data_ele.text().trim()){
                //Find group name
	                group_th_eles = $data_ele.find('th')
	                $.each(group_th_eles,function(){
	                    $group_th_ele = $(this)
	                    text = $group_th_ele.text().trim() || ""
	                    is_analysis = true
	                    data.push({'data': text, 'bold': true})
	                });
	                data_td_eles = $data_ele.find('td')
	                $.each(data_td_eles,function(){
	                    $data_td_ele = $(this)
	                    text = $data_td_ele.text().trim() || ""
	                    if ($data_td_ele && $data_td_ele[0].classList.contains('oe_number') && !$data_td_ele[0].classList.contains('oe_list_field_float_time')){
	                        text = text.replace('%', '')
	                        text = instance.web.parse_value(text, { type:"float" })
	                        data.push({'data': text || "", 'number': true})
	                    }
	                    else{
	                        data.push({'data': text})
	                    }
	                });
	                export_data.push(data)
                }
            });
            
            //Find Footer Element
            
            footer_eles = self.$el.find('.oe_list_content > tfoot> tr')
            $.each(footer_eles,function(){
                data = []
                $footer_ele = $(this)
                footer_td_eles = $footer_ele.find('td')
                $.each(footer_td_eles,function(){
                    $footer_td_ele = $(this)
                    text = $footer_td_ele.text().trim() || ""
                    if ($footer_td_ele && $footer_td_ele[0].classList.contains('oe_number')){
                        text = instance.web.parse_value(text, { type:"float" })
                        data.push({'data': text || "", 'bold': true, 'number': true})
                    }
                    else{
                        data.push({'data': text, 'bold': true})
                    }
                });
                export_data.push(data)
            });
            
            //Export to excel
            $.blockUI();
            if (export_type === 'excel'){
                 view.session.get_file({
                     url: '/web/export/zb_excel_export',
                     data: {data: JSON.stringify({
                            model : view.model,
                            headers : header_name_list,
                            rows : export_data,
                     })},
                     complete: $.unblockUI
                 });
             }
             else{
                console.log(view)
                new instance.web.Model("res.users").get_func("read")(this.session.uid, ["company_id"]).then(function(res) {
                    new instance.web.Model("res.company").get_func("read")(res['company_id'][0], ["name"]).then(function(result) {
                        view.session.get_file({
                             url: '/web/export/zb_pdf_export',
                             data: {data: JSON.stringify({
                                    uid: view.session.uid,
                                    model : view.model,
                                    headers : header_name_list,
                                    rows : export_data,
                                    company_name: result['name']
                             })},
                             complete: $.unblockUI
                         });
                    });
                });
             }
        },
        
        on_sidebar_export_view_xls: function() {
            flg=true;
	    curr_data={}
	    export_columns_keys = [];
	    export_columns_names = [];
	    export_rows = [];
	    check_count=0;
	    data_count=0;
            // Select the first list of the current (form) view
            // or assume the main view is a list view and use that
            var self = this,
            view = this.getParent(),
            children = view.getChildren();
           
            if (children) {
                children.every(function(child) {
                    if (child.field && child.field.type == 'one2many') {
                        view = child.viewmanager.views.list.controller;
                        return false; // break out of the loop
                    }
                    if (child.field && child.field.type == 'many2many') {
                        view = child.list_view;
                        return false; // break out of the loop
                    }
                    return true;
                });
            }
           
            start: 
           /* $.each(view.visible_columns, function(){
            
                if(this.tag=='field'){                	
                    // non-fields like `_group` or buttons
                    export_columns_keys.push(this.id);                    
                    export_columns_names.push(this.string);
                }
            });*/
            var column_keys = ['slno','sequence','name','severity','type','user_id','product_id','date','related_company_id','partner_id','email_from','date_closed','state','sla','comments'];
            var column_names = ['Sr. No.','Ticket No.','Title','Severity','Type','Assigned To','Product','Created On','Company Name','Contact Name','Contact Email','Resolved On','Status','SLA Compliance','Comments'];
            
            for(i=0;i<column_keys.length;i++)
            {
            	export_columns_keys.push(column_keys[i]);                    
            	export_columns_names.push({'header_name': column_names[i], 'header_data_id': column_keys[i]});
            }
            //export_columns_keys.push('categ_id');                    
            //export_columns_names.push('Category ID');
            rows = view.$el.find('.oe_list_content > tbody > tr');
            
            //var Model = new instance.web.Model('res.users');
            check_count = $('input[name="radiogroup"]:checked').length;
            total_rows = $('input[name="radiogroup"]').length;
            if(check_count<=0)
            {
            	alert('Please Select record(s) to Export');
            	return;
            }
            checkedids =[];
            $('.oe_list_content tr').each(function (i, row) {
	
        // reference all the stuff you need first
         $row = $(row),
         //       $row = $(this);
                flg=true;                
                // find only rows with data
                if($row.attr('data-id')){
              
                    export_row = [];
                    
                    checked = $row.find('th input[type=checkbox]').attr("checked");                    
                    
                    
                    if (checked === "checked"){
            	        checkedids.push(parseInt($row.attr('data-id')));
            	 	//var curr_data_obj = self.fetchval($row.attr('data-id')).then(function(res){curr_data = res;flg=false;self.loop_data(export_columns_keys,curr_data,"CRM Helpdesk");});
            	
                    }
                   
                }
                
            });
            
            if(checkedids.length>0)
            {           
                var curr_data_obj = self.fetchval(checkedids).then(function(res){curr_data = res;flg=false;self.loop_data(export_columns_keys,curr_data,"CRM Helpdesk");});
            }
           
        },
        loop_data:function(export_columns_keys_val,curr_data_vals,filename){
        export_row = [];
         $.each(curr_data_vals,function(){
         var curr_data_val=this;
         export_row = [];
         $.each(export_columns_keys_val,function(){
                            cell = curr_data_val[this];
                            if(typeof cell!='object')
                               export_row.push({'data': cell});
                            else
                               export_row.push({'data': cell[1]});   
                        });
                        export_rows.push(export_row);
                        data_count++;   
                        });
                  
                  
                  if(check_count==data_count)
                  {                  
                  //head_check = $('.oe_list_record_selector:checkbox:checked').length;
		   var self = this;
		    view = this.getParent();
		    
		 $.blockUI();
		 view.session.get_file({
                     url: '/web/export/zb_excel_export',
                     data: {data: JSON.stringify({
                            model : view.model,
		            filename: filename,
                            headers : export_columns_names,
                            rows : export_rows,
                     })},
                     complete: $.unblockUI
                 });
            }
        //return export_row;
        return;
        },
    });
};
