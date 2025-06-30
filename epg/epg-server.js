require('dotenv').config(); // Load environment variables from .env file

const express = require('express');
const bodyParser = require('body-parser');
const { exec } = require('child_process');
const fs = require('fs');
const path = require('path');
const xml2js = require('xml2js');

const app = express();
app.use(bodyParser.text({ type: 'application/xml' }));
app.use(bodyParser.json());

app.post('/generate-guide/:id', async (req, res) => {
    try {
        const channelsXmlPath = path.join(process.cwd(), 'channels.xml');
        const contentTypeHeader = req.get('Content-Type');
        const contentType = contentTypeHeader != null ? contentTypeHeader.split(';')[0] : null;
        const { id } = req.params;

        // Create directory path if it doesn't exist
        const dirPath = path.join(process.env.CONFIG_DIR, 'playlists', id);
        if (!fs.existsSync(dirPath)) {
            fs.mkdirSync(dirPath, { recursive: true });
        }

        // Save provided channels to channels.xml
        if (contentType === 'application/xml') {
            // If XML content is provided, save it directly
            fs.writeFileSync(channelsXmlPath, req.body);

            console.log(`XML received and saved to ${channelsXmlPath}`);
        } else if (contentType === 'application/json') {
            // For backward compatibility, convert JSON to XML
            try {
                const builder = new xml2js.Builder();

                // Convert JSON to XML format according to specification
                // Expected format:
                //   <channels>
                //      <channel>...</channel>
                //   </channels>
                const xmlContent = builder.buildObject(req.body);
                fs.writeFileSync(channelsXmlPath, xmlContent);

                console.log(`JSON received, converted to XML and saved to ${channelsXmlPath}`);
            } catch (error) {
                console.error(error);

                return res.status(400).json({
                    success: false,
                    error: `Failed to convert JSON to XML: ${error.message}`
                });
            }
        } else {
            console.error(`Unsupported content type: ${contentType}`);

            return res.status(400).json({ 
                success: false, 
                error: 'Unsupported content type. Please provide XML with Content-Type: application/xml or JSON with Content-Type: application/json' 
            });
        }

        // 'npm' command args
        const npmArgs = {}
        if (process.env.EPG_APP_PATH) {
            npmArgs.prefix = process.env.EPG_APP_PATH;
        }
        const npmArgsString = Object.keys(npmArgs).map(key => `--${key}=${npmArgs[key]}`).join(' ');

        // 'grab' command arguments
        const targetPath = path.join(dirPath, 'guide.xml');
        const grabArgs = {
            channels: channelsXmlPath,
            output: targetPath,
            maxConnections: process.env.MAX_CONNECTIONS,
            days: process.env.DAYS,
            timeout: process.env.TIMEOUT,
        }
        if (process.env.GZIP === 'true') {
            grabArgs.gzip = null;
        }
        const grabArgsString = Object.keys(grabArgs).map(key => grabArgs[key] ? `--${key}=${grabArgs[key]}` : `--${key}`).join(' ');

        // Run the grab command
        console.log(`Running grab command with args: ${grabArgsString} (npm args: ${npmArgsString})`);
        exec(`npm run ${npmArgsString} grab --- ${grabArgsString}`, (error, stdout, stderr) => {
            // Cleanup channels.xml
            fs.rmSync(channelsXmlPath);

            // Log stdout and stderr to make npm process output visible in server logs
            if (stdout) console.log('npm process stdout:', stdout);
            if (stderr) console.log('npm process stderr:', stderr);

            if (error) {
                console.error(error);
                return res.status(500).json({ success: false, error: error.message });
            }

            // Check if guide was generated
            if (fs.existsSync(targetPath)) {
                console.log('Guide generated');
                return res.json({ success: true });
            } else {
                console.warn('Guide not generated');
                return res.status(500).json({ success: false, error: 'Guide not generated' });
            }
        });
    } catch (err) {
        console.error(err);
        res.status(500).json({ success: false, error: err.message });
    }
});

app.listen(3000, () => {
    console.log('EPG service listening on port 3000');
});
