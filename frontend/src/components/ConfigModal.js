import { useState, useEffect } from "react";
import axios from "axios";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { Key, Percent } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const ConfigModal = ({ open, onClose, onSave, currentConfig }) => {
  const [apiKey, setApiKey] = useState("");
  const [sobrepreco, setSobrepreco] = useState(135);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (currentConfig && currentConfig.configured) {
      setSobrepreco(currentConfig.sobrepreco_padrao || 135);
    }
  }, [currentConfig]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!apiKey.trim()) {
      toast.error("Por favor, insira a API Key da Intelipost");
      return;
    }

    if (sobrepreco < 0) {
      toast.error("O sobrepreço não pode ser negativo");
      return;
    }

    setLoading(true);
    try {
      await axios.post(`${API}/config/intelipost`, {
        api_key_intelipost: apiKey,
        sobrepreco_padrao: parseFloat(sobrepreco),
      });
      onSave();
      setApiKey("");
    } catch (error) {
      console.error("Erro ao salvar configuração:", error);
      toast.error("Erro ao salvar configuração: " + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[500px] bg-white">
        <DialogHeader>
          <DialogTitle className="text-xl font-bold text-slate-900">Configurações da API</DialogTitle>
          <DialogDescription className="text-slate-600">
            Configure sua API Key da Intelipost e o sobrepreço padrão
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-6 py-4">
          <div className="space-y-2">
            <Label htmlFor="api-key" className="text-sm font-semibold text-slate-700 flex items-center gap-2">
              <Key className="h-4 w-4" />
              API Key Intelipost
            </Label>
            <Input
              id="api-key"
              data-testid="input-api-key"
              type="password"
              placeholder="Digite sua API Key"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              className="bg-white border-slate-200"
            />
            {currentConfig?.configured && (
              <p className="text-xs text-slate-500">
                API Key atual: {currentConfig.api_key_masked}
              </p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="sobrepreco" className="text-sm font-semibold text-slate-700 flex items-center gap-2">
              <Percent className="h-4 w-4" />
              Sobrepreço Padrão (%)
            </Label>
            <Input
              id="sobrepreco"
              data-testid="input-sobrepreco"
              type="number"
              step="0.01"
              placeholder="135"
              value={sobrepreco}
              onChange={(e) => setSobrepreco(e.target.value)}
              className="bg-white border-slate-200"
            />
            <p className="text-xs text-slate-500">
              Exemplo: 135% significa que o preço final será 2,35x o valor base
            </p>
          </div>

          <DialogFooter className="gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={loading}
              className="border-slate-200"
            >
              Cancelar
            </Button>
            <Button
              data-testid="btn-save-config"
              type="submit"
              disabled={loading}
              className="bg-blue-600 hover:bg-blue-700 text-white"
            >
              {loading ? "Salvando..." : "Salvar Configuração"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export default ConfigModal;