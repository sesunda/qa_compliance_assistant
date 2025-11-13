const fs = require('fs');
const ExcelJS = require('exceljs');

async function createExcelFromJson(jsonFilePath, outputExcelPath) {
    console.log(`📖 Reading JSON file: ${jsonFilePath}`);
    const data = JSON.parse(fs.readFileSync(jsonFilePath, 'utf8'));
    
    const workbook = new ExcelJS.Workbook();
    
    // Create Cover Page
    console.log('📄 Creating Cover Page...');
    const coverSheet = workbook.addWorksheet('Cover Page');
    const coverData = data.cover_page || {};
    
    coverSheet.getCell('A1').value = coverData.title || 'IM8 Assessment';
    coverSheet.getCell('A1').font = { bold: true, size: 16 };
    
    const coverInfo = [
        ['Agency:', coverData.agency_name || ''],
        ['Assessment Period:', coverData.assessment_period || ''],
        ['Prepared By:', coverData.prepared_by || ''],
        ['Preparation Date:', coverData.preparation_date || ''],
        ['Reviewed By:', coverData.reviewed_by || ''],
        ['Review Date:', coverData.review_date || ''],
        ['Approval Status:', coverData.approval_status || '']
    ];
    
    let row = 3;
    coverInfo.forEach(([label, value]) => {
        coverSheet.getCell(`A${row}`).value = label;
        coverSheet.getCell(`A${row}`).font = { bold: true };
        coverSheet.getCell(`B${row}`).value = value;
        row++;
    });
    
    // Add instructions
    if (data.instructions) {
        const instructions = data.instructions;
        coverSheet.getCell(`A${row + 1}`).value = 'Instructions:';
        coverSheet.getCell(`A${row + 1}`).font = { bold: true, size: 12 };
        row += 2;
        
        coverSheet.getCell(`A${row}`).value = instructions.overview || '';
        coverSheet.getCell(`A${row}`).alignment = { wrapText: true };
        row += 2;
        
        if (instructions.completion_steps) {
            coverSheet.getCell(`A${row}`).value = 'Completion Steps:';
            coverSheet.getCell(`A${row}`).font = { bold: true };
            row++;
            instructions.completion_steps.forEach(step => {
                coverSheet.getCell(`A${row}`).value = step;
                row++;
            });
        }
    }
    
    coverSheet.getColumn('A').width = 20;
    coverSheet.getColumn('B').width = 50;
    
    // Create domain sheets
    const domains = data.domains || [];
    console.log(`📊 Creating ${domains.length} domain sheets...`);
    
    for (const domain of domains) {
        const domainId = domain.domain_id || 'Unknown';
        const domainName = domain.domain_name || 'Unknown';
        const sheetName = domainId.substring(0, 31);
        
        console.log(`  → ${sheetName}: ${domainName}`);
        const ws = workbook.addWorksheet(sheetName);
        
        // Domain header
        ws.getCell('A1').value = `${domainId}: ${domainName}`;
        ws.getCell('A1').font = { bold: true, color: { argb: 'FFFFFFFF' }, size: 12 };
        ws.getCell('A1').fill = {
            type: 'pattern',
            pattern: 'solid',
            fgColor: { argb: 'FF4472C4' }
        };
        ws.mergeCells('A1:H1');
        
        ws.getCell('A2').value = domain.description || '';
        ws.getCell('A2').alignment = { wrapText: true };
        ws.mergeCells('A2:H2');
        ws.getRow(2).height = 30;
        
        // Headers
        const headers = ['Control ID', 'Control Name', 'Description', 'Implementation Status', 
                        'Evidence Reference', 'Evidence Files', 'Notes', 'Last Review'];
        
        headers.forEach((header, idx) => {
            const cell = ws.getCell(4, idx + 1);
            cell.value = header;
            cell.font = { bold: true, color: { argb: 'FFFFFFFF' } };
            cell.fill = {
                type: 'pattern',
                pattern: 'solid',
                fgColor: { argb: 'FF366092' }
            };
            cell.alignment = { horizontal: 'center', vertical: 'middle', wrapText: true };
            cell.border = {
                top: { style: 'thin' },
                left: { style: 'thin' },
                bottom: { style: 'thin' },
                right: { style: 'thin' }
            };
        });
        
        // Add controls
        const controls = domain.controls || [];
        let rowNum = 5;
        
        for (const control of controls) {
            ws.getCell(rowNum, 1).value = control.control_id || '';
            ws.getCell(rowNum, 2).value = control.control_name || '';
            ws.getCell(rowNum, 3).value = control.description || '';
            ws.getCell(rowNum, 4).value = control.implementation_status || '';
            ws.getCell(rowNum, 5).value = control.evidence_reference || '';
            
            // Evidence files
            const evidenceFiles = control.evidence_files || [];
            if (evidenceFiles.length > 0) {
                const filesText = evidenceFiles.map(ef => 
                    `• ${typeof ef === 'object' ? ef.filename : ef}`
                ).join('\n');
                ws.getCell(rowNum, 6).value = filesText;
            }
            
            ws.getCell(rowNum, 7).value = control.notes || '';
            ws.getCell(rowNum, 8).value = control.last_review_date || '';
            
            // Apply borders and alignment
            for (let col = 1; col <= 8; col++) {
                const cell = ws.getCell(rowNum, col);
                cell.border = {
                    top: { style: 'thin' },
                    left: { style: 'thin' },
                    bottom: { style: 'thin' },
                    right: { style: 'thin' }
                };
                cell.alignment = { vertical: 'top', wrapText: true };
            }
            
            ws.getRow(rowNum).height = 60;
            rowNum++;
        }
        
        // Set column widths
        ws.getColumn(1).width = 12;
        ws.getColumn(2).width = 30;
        ws.getColumn(3).width = 40;
        ws.getColumn(4).width = 18;
        ws.getColumn(5).width = 20;
        ws.getColumn(6).width = 25;
        ws.getColumn(7).width = 40;
        ws.getColumn(8).width = 12;
    }
    
    // Create Summary Dashboard
    console.log('📈 Creating Summary Dashboard...');
    const summarySheet = workbook.addWorksheet('Summary Dashboard');
    const summaryData = data.summary_dashboard || {};
    
    summarySheet.getCell('A1').value = 'IM8 Assessment Summary Dashboard';
    summarySheet.getCell('A1').font = { bold: true, size: 14 };
    summarySheet.mergeCells('A1:B1');
    
    const summaryItems = [
        ['Total Controls:', summaryData.total_controls || 0],
        ['Completion Percentage:', `${summaryData.completion_percentage || 0}%`],
        ['Domains Completed:', summaryData.domains_completed || 0],
        ['Evidence Items Attached:', summaryData.evidence_items_attached || 0],
        ['Validation Status:', summaryData.validation_status || ''],
        ['Last Updated:', summaryData.last_updated || ''],
        ['Submitted By:', summaryData.submitted_by || ''],
        ['Submission Date:', summaryData.submission_date || '']
    ];
    
    row = 3;
    summaryItems.forEach(([label, value]) => {
        summarySheet.getCell(`A${row}`).value = label;
        summarySheet.getCell(`A${row}`).font = { bold: true };
        summarySheet.getCell(`B${row}`).value = value;
        row++;
    });
    
    // Controls by status
    if (summaryData.controls_by_status) {
        row++;
        summarySheet.getCell(`A${row}`).value = 'Controls by Status:';
        summarySheet.getCell(`A${row}`).font = { bold: true, size: 12 };
        row++;
        
        Object.entries(summaryData.controls_by_status).forEach(([status, count]) => {
            summarySheet.getCell(`A${row}`).value = status.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
            summarySheet.getCell(`B${row}`).value = count;
            row++;
        });
    }
    
    summarySheet.getColumn('A').width = 25;
    summarySheet.getColumn('B').width = 30;
    
    // Save workbook
    console.log(`💾 Saving Excel file: ${outputExcelPath}`);
    await workbook.xlsx.writeFile(outputExcelPath);
    console.log(`✅ Excel file created successfully!`);
}

async function main() {
    console.log('='.repeat(60));
    console.log('IM8 JSON to Excel Converter (Node.js)');
    console.log('='.repeat(60));
    console.log();
    
    const templateJson = 'storage/IM8_Assessment_Template.json';
    const completedJson = 'storage/IM8_Security_Awareness_Training_Completed.json';
    
    const templateExcel = 'storage/IM8_Assessment_Template.xlsx';
    const completedExcel = 'storage/IM8_Security_Awareness_Training_Completed.xlsx';
    
    try {
        // Convert template
        if (fs.existsSync(templateJson)) {
            console.log('🔄 Converting Template JSON to Excel...');
            await createExcelFromJson(templateJson, templateExcel);
            console.log();
        } else {
            console.log(`⚠️  Template JSON not found: ${templateJson}`);
            console.log();
        }
        
        // Convert completed assessment
        if (fs.existsSync(completedJson)) {
            console.log('🔄 Converting Completed Assessment JSON to Excel...');
            await createExcelFromJson(completedJson, completedExcel);
            console.log();
        } else {
            console.log(`⚠️  Completed JSON not found: ${completedJson}`);
            console.log();
        }
        
        console.log('='.repeat(60));
        console.log('✅ Conversion Complete!');
        console.log('='.repeat(60));
        console.log();
        console.log('📁 Generated Files:');
        if (fs.existsSync(templateExcel)) {
            console.log(`  1. ${templateExcel}`);
        }
        if (fs.existsSync(completedExcel)) {
            console.log(`  2. ${completedExcel}`);
        }
        console.log();
        console.log('📝 Next Steps:');
        console.log('  1. Open the Excel files to review the structure');
        console.log('  2. Template file can be shared with Analysts');
        console.log('  3. Completed file shows example submission with data');
        console.log();
    } catch (error) {
        console.error('❌ Error:', error.message);
        process.exit(1);
    }
}

main();
