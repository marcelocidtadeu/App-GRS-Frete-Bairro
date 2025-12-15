import { useState } from "react";
import axios from "axios";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { FileSpreadsheet, AlertCircle, CheckCircle } from "lucide-react";
import { toast } from "sonner";
import LogsConsole from "@/components/LogsConsole";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const CotacaoTab = ({ config, onComplete }) => {
  const [mainFile, setMainFile] = useState(null);
  const [sobrepreco, setSobrepreco] = useState(config?.sobrepreco_padrao || 135);
  const [processing, setProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [logs, setLogs] = useState([]);
  const [result, setResult] = useState(null);

  const handleMainFileDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file && file.name.endsWith('.xlsx')) {
      setMainFile(file);
      toast.success(`Arquivo selecionado: ${file.name}`);
    } else {
      toast.error("Por favor, selecione um arquivo .xlsx");
    }
  };

  const handleProcess = async () => {
    if (!config?.configured) {
      toast.error("Configure a API Key da Intelipost antes de processar");
      return;
    }

    if (!mainFile) {
      toast.error("Selecione um arquivo para processar");
      return;
    }

    setProcessing(true);
    setProgress(10);
    setLogs([["info", "Iniciando processamento..."]]);
    setResult(null);

    try {
      const formData = new FormData();
      formData.append("file", mainFile);
      formData.append("sobrepreco", sobrepreco);

      setProgress(30);
      setLogs(prev => [...prev, ["info", "Enviando arquivo para o servidor..."]]);

      const response = await axios.post(`${API}/cotacao/process`, formData, {
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
      setLogs(prev => [...prev, ["success", "Processamento concluído com sucesso!"]]);

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `resultado-cotacao-${new Date().getTime()}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();

      setProgress(100);
      setLogs(prev => [...prev, ["success", "Download iniciado!"]]);
      setResult({ success: true });
      
      toast.success("Processamento concluído! O arquivo foi baixado.");
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
      {/* Configuração */}
      <Card className="bg-white rounded-xl shadow-sm hover:shadow-md transition-shadow" style={{borderColor: '#e2e8f0'}}>
        <CardHeader className="border-b" style={{borderColor: '#f1f5f9', backgroundColor: '#f8fafc'}}>
          <CardTitle style={{color: '#001e5a'}}>Configuração de Cotação</CardTitle>
          <CardDescription>Configure o sobrepreço para este processamento</CardDescription>
        </CardHeader>
        <CardContent className="p-6 space-y-4">
          <div className="space-y-2">
            <Label htmlFor="sobrepreco-cotacao" className="text-sm font-semibold uppercase tracking-wider" style={{color: '#64748b'}}>
              Sobrepreço (%)
            </Label>
            <Input
              id="sobrepreco-cotacao"
              data-testid="input-sobrepreco-cotacao"
              type="number"
              step="0.01"
              value={sobrepreco}
              onChange={(e) => setSobrepreco(e.target.value)}
              disabled={processing}
              className="bg-white"
              style={{borderColor: '#e2e8f0'}}
            />
          </div>
        </CardContent>
      </Card>

      {/* Upload Principal */}
      <Card className="bg-white rounded-xl shadow-sm hover:shadow-md transition-shadow" style={{borderColor: '#e2e8f0'}}>
        <CardHeader className="border-b" style={{borderColor: '#f1f5f9', backgroundColor: '#f8fafc'}}>
          <CardTitle style={{color: '#001e5a'}}>Upload da Planilha</CardTitle>
          <CardDescription>Arraste ou selecione o arquivo Excel com os dados de cotação</CardDescription>
        </CardHeader>
        <CardContent className="p-6">
          <div
            data-testid="dropzone-main"
            onDrop={handleMainFileDrop}
            onDragOver={(e) => e.preventDefault()}
            className="border-2 border-dashed rounded-lg p-12 text-center hover:bg-blue-50 transition-all cursor-pointer"
            style={{borderColor: '#cbd5e1'}}
            onClick={() => document.getElementById('main-file-input').click()}
          >
            <FileSpreadsheet className="h-12 w-12 mx-auto mb-4" style={{color: '#94a3b8'}} />
            <p className="text-lg font-medium mb-2" style={{color: '#334155'}}>
              {mainFile ? mainFile.name : "Arraste o arquivo aqui"}
            </p>
            <p className="text-sm" style={{color: '#64748b'}}>ou clique para selecionar</p>
            <input
              id="main-file-input"
              type="file"
              accept=".xlsx"
              className="hidden"
              onChange={(e) => setMainFile(e.target.files[0])}
              disabled={processing}
            />
          </div>

          {mainFile && (
            <div className="mt-4 flex justify-between items-center">
              <span className="text-sm" style={{color: '#64748b'}}>Arquivo pronto para processamento</span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setMainFile(null)}
                disabled={processing}
                style={{borderColor: '#e2e8f0'}}
              >
                Remover
              </Button>
            </div>
          )}

          <Button
            data-testid="btn-process-cotacao"
            onClick={handleProcess}
            disabled={!mainFile || processing}
            className="w-full mt-6 font-medium py-6 active:scale-95 transition-all text-white hover:opacity-90"
            style={{backgroundColor: '#ff7a3d'}}
          >
            {processing ? "Processando..." : "Executar Cotações"}
          </Button>
        </CardContent>
      </Card>

      {/* Progress & Logs */}
      {processing && (
        <Card className="bg-white rounded-xl shadow-sm" style={{borderColor: '#e2e8f0'}}>
          <CardHeader className="border-b" style={{borderColor: '#f1f5f9', backgroundColor: '#f8fafc'}}>
            <CardTitle style={{color: '#001e5a'}}>Progresso</CardTitle>
          </CardHeader>
          <CardContent className="p-6 space-y-4">
            <div className="space-y-2">
              <div className="flex justify-between text-sm" style={{color: '#64748b'}}>
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
            {result.success ? "Processamento concluído com sucesso!" : `Erro: ${result.error}`}
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
};

export default CotacaoTab;