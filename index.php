<?php
// List of available files for download
$files = [
    "togo.csv" => "csv_exports/togo.csv",
    "kolba.csv" => "csv_exports/kolba.csv",
    "spc.csv" => "csv_exports/spc.csv"
];

// Static tokens for each file download
$static_tokens = [
    "togo.csv" => "6b3a55e0264e2e1d57f03d03d8cf72ed", // Pre-generated static token for Togo
    "kolba.csv" => "d3b07384d113edec49eaa6238ad5ff00", // Pre-generated static token for Kolba
    "spc.csv" => "51be56c5eae41b0b877d44f3fe1fe134"  // Pre-generated static token for SPC
];

// Function to validate the static token
function isValidDownload($file_name, $token) {
    global $static_tokens;
    return isset($static_tokens[$file_name]) && $static_tokens[$file_name] === $token;
}

// Handle file download based on URL path
if (isset($_SERVER['REQUEST_URI'])) {
    // Parse the URL path
    $url_path = trim(parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH), '/');
    
    // Extract file name and token from the URL
    $path_parts = explode('/', $url_path);
    
    if (count($path_parts) == 2) {
        $file_name = $path_parts[0]; // The file name part
        $token = $path_parts[1];     // The token part
        
        // Check if the file exists and if the token is valid
        if (array_key_exists($file_name, $files) && isValidDownload($file_name, $token)) {
            $file_path = $files[$file_name];

            // Check if the file exists
            if (file_exists($file_path)) {
                echo "File: " . htmlspecialchars($file_name) . "dowloaded";
                // Set headers for download
                header('Content-Description: File Transfer');
                header('Content-Type: application/octet-stream');
                header('Content-Disposition: attachment; filename="' . basename($file_path) . '"');
                header('Content-Length: ' . filesize($file_path));

                // Read and output the file
                readfile($file_path);
                exit; // Exit after download
            } else {
                echo "File does not exist.";
            }
        } else {
            echo "Invalid download link.";
        }
    } else {
        echo "Invalid URL format.";
    }
}
?>
