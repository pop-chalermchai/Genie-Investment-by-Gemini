const fs = require('fs');
try {
    const code = fs.readFileSync('app.js', 'utf-8');
    const start = code.indexOf('const researchReports = {');
    // Find the end marker
    const endStr = '\n// ==========================================================================\n// CORE WORKSPACE INITIALIZATION';
    let end = code.indexOf(endStr);
    if (end === -1) {
        // Fallback search
        end = code.indexOf('};\n\n//');
    } else {
        // adjust end to include the '};'
        end = code.lastIndexOf('};', end) + 1;
    }
    
    const jsObjectString = code.substring(start + 'const researchReports = '.length, end + 1);
    
    // Evaluate the object string
    const reports = eval('(' + jsObjectString + ')');
    
    fs.writeFileSync('reports.json', JSON.stringify(reports, null, 2));
    console.log("Successfully extracted to reports.json");
} catch(e) {
    console.error("Error:", e);
}
