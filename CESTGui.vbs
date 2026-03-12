Dim objShell, objFSO, strPath
Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

' 获取脚本所在目录
strPath = objFSO.GetParentFolderName(WScript.ScriptFullName)

' 启动应用
On Error Resume Next
objShell.Run """" & strPath & "\.venv\Scripts\python.exe"" """ & strPath & "\main.py""", 0, False

' 如果出错，显示消息
If Err.Number <> 0 Then
    MsgBox "无法启动CEST GUI应用" & vbCrLf & "错误: " & Err.Description, vbCritical, "启动失败"
End If
