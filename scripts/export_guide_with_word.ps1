param([Parameter(Mandatory=$true)][string]$InputDocx,
      [Parameter(Mandatory=$true)][string]$OutputPdf)
$ErrorActionPreference = 'Stop'
$guideWord = $null
$guideDocument = $null
try {
    $guideWord = New-Object -ComObject Word.Application
    $guideWord.Visible = $false
    $guideWord.DisplayAlerts = 0
    $guideWord.AutomationSecurity = 3
    $guideDocument = $guideWord.Documents.Open($InputDocx, $false, $true, $false)
    $guideDocument.Fields.Update() | Out-Null
    $guideDocument.Repaginate()
    $guideDocument.ExportAsFixedFormat($OutputPdf, 17)
    Write-Output ('Rendered pages: ' + $guideDocument.ComputeStatistics(2))
} finally {
    if ($null -ne $guideDocument) {
        $guideDocument.Close(0)
        [System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($guideDocument) | Out-Null
    }
    if ($null -ne $guideWord) {
        $guideWord.Quit()
        [System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($guideWord) | Out-Null
    }
}
