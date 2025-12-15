import { useState } from "react";
import axios from "axios";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Upload, FileSpreadsheet, AlertCircle, CheckCircle } from "lucide-react";
import { toast } from "sonner";
import LogsConsole from "@/components/LogsConsole";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const CepTab = ({ onComplete }) => {
  const [file, setFile] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [logs, setLogs] = useState([]);
  const [result, setResult] = useState(null);

  const handleFileDrop = (e) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && droppedFile.name.endsWith('.xlsx')) {
      setFile(droppedFile);
      toast.success(`Arquivo selecionado: ${droppedFile.name}`);
    } else {
      toast.error("Por favor, selecione um arquivo .xlsx");
    }
  };

  const handleProcess = async () => {
    if (!file) {
      toast.error("Selecione um arquivo para processar");
      return;
    }

    setProcessing(true);
    setProgress(10);
    setLogs([["info", "Iniciando busca de CEPs..."]]);
    setResult(null);

    try {
      const formData = new FormData();
      formData.append("file", file);

      setProgress(30);
      setLogs(prev => [...prev, ["info", "Enviando arquivo para o servidor..."]]);

      const response = await axios.post(`${API}/cep/process`, formData, {
        responseType: 'blob',
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setProgress(30 + percentCompleted * 0.3);
        },
      });

      setProgress(90);
      setLogs(prev => [...prev, ["success", "Busca concluída com sucesso!"]]);

      // Download do arquivo
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `resultado-cep-${new Date().getTime()}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();

      setProgress(100);
      setLogs(prev => [...prev, ["success", "Download iniciado!"]]);
      setResult({ success: true });
      
      toast.success("Busca concluída! O arquivo foi baixado.");
      onComplete();

    } catch (error) {
      console.error("Erro ao processar:", error);
      setLogs(prev => [...prev, ["error", `Erro: ${error.response?.data?.detail || error.message}`]]);
      toast.error("Erro ao processar: " + (error.response?.data?.detail || error.message));
      setResult({ success: false, error: error.message });
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Upload */}
      <Card className="bg-white border-slate-200 rounded-xl shadow-sm hover:shadow-md transition-shadow">
        <CardHeader className="border-b border-slate-100 bg-slate-50/50">
          <CardTitle className="text-slate-900">Upload da Planilha</CardTitle>
          <CardDescription>Arraste ou selecione o arquivo Excel com os CEPs</CardDescription>
        </CardHeader>
        <CardContent className="p-6">
          <div
            data-testid="dropzone-cep"
            onDrop={handleFileDrop}
            onDragOver={(e) => e.preventDefault()}
            className="border-2 border-dashed border-slate-300 rounded-lg p-12 text-center hover:border-blue-500 hover:bg-blue-50 transition-all cursor-pointer"
            onClick={() => document.getElementById('cep-file-input').click()}
          >
            <FileSpreadsheet className="h-12 w-12 mx-auto text-slate-400 mb-4" />
            <p className="text-lg font-medium text-slate-700 mb-2">
              {file ? file.name : "Arraste o arquivo aqui"}
            </p>
            <p className="text-sm text-slate-500">ou clique para selecionar</p>
            <input
              id="cep-file-input"
              type="file"
              accept=".xlsx"
              className="hidden"
              onChange={(e) => setFile(e.target.files[0])}
              disabled={processing}
            />
          </div>

          {file && (
            <div className="mt-4 flex justify-between items-center">
              <span className="text-sm text-slate-600">Arquivo pronto para processamento</span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setFile(null)}
                disabled={processing}
              >
                Remover
              </Button>
            </div>
          )}

          <Button
            data-testid="btn-process-cep"
            onClick={handleProcess}
            disabled={!file || processing}
            className="w-full mt-6 bg-blue-600 hover:bg-blue-700 text-white font-medium py-6 active:scale-95 transition-all"
          >
            {processing ? "Processando..." : "Buscar Bairros"}
          </Button>
        </CardContent>
      </Card>

      {/* Informações */}
      <Card className="bg-blue-50 border-blue-200 rounded-xl">
        <CardContent className="p-6">
          <h3 className="font-semibold text-blue-900 mb-2">Formato esperado da planilha:</h3>
          <ul className="list-disc list-inside text-sm text-blue-800 space-y-1">
            <li>Coluna obrigatória: <strong>CEP</strong></li>
            <li>CEPs serão normalizados automaticamente (apenas números)</li>
            <li>O resultado incluirá: Bairro, Cidade e UF</li>
            <li>CEPs inválidos serão listados em uma aba separada</li>
          </ul>
        </CardContent>
      </Card>

      {/* Progress & Logs */}
      {processing && (
        <Card className="bg-white border-slate-200 rounded-xl shadow-sm">
          <CardHeader className="border-b border-slate-100 bg-slate-50/50">
            <CardTitle className="text-slate-900">Progresso</CardTitle>
          </CardHeader>
          <CardContent className="p-6 space-y-4">
            <div className="space-y-2">
              <div className="flex justify-between text-sm text-slate-600">
                <span>Processando...</span>
                <span>{Math.round(progress)}%</span>
              </div>
              <Progress value={progress} className="h-2" />
            </div>
            <LogsConsole logs={logs} />
          </CardContent>
        </Card>
      )}

      {/* Result */}
      {result && !processing && (
        <Alert className={result.success ? "border-emerald-200 bg-emerald-50" : "border-rose-200 bg-rose-50"}>
          {result.success ? <CheckCircle className="h-4 w-4 text-emerald-600" /> : <AlertCircle className="h-4 w-4 text-rose-600" />}
          <AlertDescription className={result.success ? "text-emerald-600" : "text-rose-600"}>
            {result.success ? "Busca concluída com sucesso!" : `Erro: ${result.error}`}
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
};

export default CepTab;