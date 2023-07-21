// Load the Google Cloud Storage API
gapi.load('client', init);

function init() {
  gapi.client.init({
    apiKey: '84f934357826fb64c7e535e83c71341f1c3e1aa3',
    clientId: '116954764849147438391',
    discoveryDocs: ['https://www.googleapis.com/discovery/v1/apis/storage/v1/rest'],
    scope: 'https://www.googleapis.com/auth/cloud-platform'
  }).then(function() {
    // API client loaded successfully
    listBucketFiles();
  }, function(error) {
    // Error loading API client
    console.log('Error loading GAPI client:', error);
  });
}

function listBucketFiles() {
  gapi.client.storage.objects.list({
    bucket: 'YOUR_BUCKET_NAME'
  }).then(function(response) {
    var files = response.result.items;
    files.forEach(function(file) {
        // put the file names into the div called 'output'
        document.getElementById('output').innerHTML += file.name + '<br>';
      // You can process the file names as per your requirement
    });
  }, function(error) {
    console.log('Error listing bucket files:', error);
  });
}
