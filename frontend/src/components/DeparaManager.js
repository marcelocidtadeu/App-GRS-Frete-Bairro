import { useState, useEffect } from "react";
import axios from "axios";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Upload, CheckCircle, AlertCircle, RefreshCw } from "lucide-react";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const DeparaManager = () => {
  const [deparaStatus, setDeparaStatus] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [file, setFile] = useState(null);

  useEffect(() => {
    loadDeparaStatus();
  }, []);

  const loadDeparaStatus = async () => {
    try {
      const response = await axios.get(`${API}/depara/status`);
      setDeparaStatus(response.data);
    } catch (error) {
      console.error("Erro ao carregar status do DE-PARA:", error);
    }
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile && selectedFile.name.endsWith('.xlsx')) {
      setFile(selectedFile);
    } else {
      toast.error("Por favor, selecione um arquivo .xlsx");
    }
  };

  const handleUpload = async () => {
    if (!file) {
      toast.error("Selecione um arquivo primeiro");
      return;
    }

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await axios.post(`${API}/depara/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      toast.success(response.data.message);
      setFile(null);
      loadDeparaStatus();
    } catch (error) {
      console.error("Erro ao fazer upload do DE-PARA:", error);
      toast.error("Erro ao fazer upload: " + (error.response?.data?.detail || error.message));
    } finally {
      setUploading(false);
    }
  };

  return (
    <Card className="bg-white rounded-xl shadow-sm hover:shadow-md transition-shadow" style={{borderColor: '#e2e8f0'}}>
      <CardHeader className="border-b" style={{borderColor: '#f1f5f9', backgroundColor: '#f8fafc'}}>
        <CardTitle style={{color: '#001e5a'}}>Planilha DE-PARA (Mapeamento de Transportadoras)</CardTitle>
        <CardDescription>Carregue uma vez e use em todas as cotações. Atualize apenas quando necessário.</CardDescription>
      </CardHeader>
      <CardContent className="p-6 space-y-4">
        {deparaStatus?.configured && (
          <Alert className="border-emerald-200 bg-emerald-50">
            <CheckCircle className="h-4 w-4 text-emerald-600" />
            <AlertDescription className="text-emerald-700">
              DE-PARA configurado com <strong>{deparaStatus.count}</strong> mapeamentos.
              {deparaStatus.updated_at && (
                <span className="block text-sm mt-1">
                  Última atualização: {new Date(deparaStatus.updated_at).toLocaleString('pt-BR')}
                </span>
              )}
            </AlertDescription>
          </Alert>
        )}

        {!deparaStatus?.configured && (
          <Alert className="border-amber-200 bg-amber-50">
            <AlertCircle className="h-4 w-4 text-amber-600" />
            <AlertDescription className="text-amber-700">
              Nenhuma planilha DE-PARA carregada. As cotações funcionarão normalmente, mas sem mapeamento ERP.
            </AlertDescription>
          </Alert>
        )}

        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Button
              data-testid="btn-select-depara"
              variant="outline"
              onClick={() => document.getElementById('depara-file-input').click()}
              disabled={uploading}
              className="flex-1"
              style={{borderColor: '#e2e8f0'}}
            >
              <Upload className="h-4 w-4 mr-2" />
              {file ? file.name : "Selecionar Arquivo DE-PARA"}
            </Button>
            <input
              id="depara-file-input"
              type="file"
              accept=".xlsx"
              className="hidden"
              onChange={handleFileChange}
              disabled={uploading}
            />
            {file && (
              <Button
                data-testid="btn-upload-depara"
                onClick={handleUpload}
                disabled={uploading}
                style={{backgroundColor: '#ff7a3d', color: 'white'}}
                className="hover:opacity-90"
              >
                {uploading ? (
                  <RefreshCw className="h-4 w-4 animate-spin" />
                ) : (
                  "Carregar"
                )}
              </Button>
            )}
          </div>
          <p className="text-xs" style={{color: '#64748b'}}>
            O arquivo DE-PARA deve conter as colunas: <strong>intelipost</strong> (ou transportadora), <strong>erp</strong>, e <strong>codigo_erp</strong>
          </p>
        </div>
      </CardContent>
    </Card>
  );
};

export default DeparaManager;